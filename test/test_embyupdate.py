from __future__ import (division, absolute_import, print_function,
                        unicode_literals)

from test._common import unittest
from test.helper import TestHelper
from beetsplug import embyupdate
import responses


class EmbyUpdateTest(unittest.TestCase, TestHelper):
    def setUp(self):
        self.setup_beets()
        self.load_plugins('embyupdate')

        self.config['emby'] = {
            u'host': u'localhost',
            u'port': 8096,
            u'username': u'username',
            u'password': u'password'
        }

    def tearDown(self):
        self.teardown_beets()
        self.unload_plugins()

    def test_api_url(self):
        self.assertEqual(
            embyupdate.api_url(self.config['emby']['host'].get(),
                               self.config['emby']['port'].get(),
                               '/Library/Refresh'),
            'http://localhost:8096/Library/Refresh?format=json'
        )

    def test_password_data(self):
        self.assertEqual(
            embyupdate.password_data(self.config['emby']['username'].get(),
                                     self.config['emby']['password'].get()),
            {
                'username': 'username',
                'password': '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8',
                'passwordMd5': '5f4dcc3b5aa765d61d8327deb882cf99'
            }
        )

    def test_create_header_no_token(self):
        self.assertEqual(
            embyupdate.create_headers('e8837bc1-ad67-520e-8cd2-f629e3155721'),
            {
                'Authorization': 'MediaBrowser',
                'UserId': 'e8837bc1-ad67-520e-8cd2-f629e3155721',
                'Client': 'other',
                'Device': 'empy',
                'DeviceId': 'beets',
                'Version': '0.0.0'
            }
        )
