import pytest
import jwt
import mock
import responses
from django.test import TestCase
from django.core.management import call_command
from course_discovery.apps.publisher.management.commands.load_drupal_data import DrupalCourseMarketingSiteDataLoader
from course_discovery.apps.core.tests.factories import PartnerFactory
from course_discovery.apps.core.tests.utils import mock_api_callback

ACCESS_TOKEN = str(jwt.encode({'preferred_username': 'bob'}, 'secret'), 'utf-8')


class TestLoadDrupalData(TestCase):
    def setUp(self):
        super(TestLoadDrupalData, self).setUp()
        self.command_name = 'load_drupal_data'
        self.partner = PartnerFactory()

    def mock_access_token_api(self, requests_mock=None):
        body = {
            'access_token': ACCESS_TOKEN,
            'expires_in': 30
        }
        requests_mock = requests_mock or responses

        url = self.partner.oidc_url_root.strip('/') + '/access_token'
        requests_mock.add_callback(
            responses.POST,
            url,
            callback=mock_api_callback(url, body, results_key=False),
            content_type='application/json'
        )

        return body

    def test_load_drupal_data_with_partner(self):
        with responses.RequestsMock() as rsps:
            self.mock_access_token_api(rsps)

            with mock.patch('course_discovery.apps.publisher.management.commands.'
                            'load_drupal_data.execute_loader') as mock_executor:
                course_ids = 'course-v1:SC+BreadX+3T2015'
                command_args = ['--course_ids={course_ids}'.format(
                    course_ids=course_ids,), '--partner_code={partner_code}'.format(
                    partner_code=self.partner.short_code
                )]
                call_command('load_drupal_data', *command_args)

                expected_calls = [
                mock.call(DrupalCourseMarketingSiteDataLoader,
                          self.partner,
                          self.partner.marketing_site_url_root,
                          ACCESS_TOKEN,
                          'JWT',
                          1,
                          False,
                          set(course_ids.split(',')),
                          username=jwt.decode(ACCESS_TOKEN, verify=False)['preferred_username'])]
                mock_executor.assert_has_calls(expected_calls)
