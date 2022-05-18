import unittest

import mock
import requests

import parsers.lib.utils as tested


class UtilsTestCase(unittest.TestCase):
    """
    Tests for fetch_production.
    Patches in a fake response from the data source to allow repeatable testing.
    """

    def test_TOKEN_WIKI_URL(self):
        self.assertEqual(requests.get(tested.TOKEN_WIKI_URL).status_code, 200)

    def test_get_token(self):
        with mock.patch.dict("parsers.lib.utils.os.environ", {"token": "42"}):
            self.assertEqual(tested.get_token("token"), "42")

        with mock.patch.dict("parsers.lib.utils.os.environ", {}):
            with self.assertRaises(Exception):
                tested.get_token("token")

        with mock.patch.dict("parsers.lib.utils.os.environ", {"token": ""}):
            with self.assertRaises(Exception):
                tested.get_token("token")
