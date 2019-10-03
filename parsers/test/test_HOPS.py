import unittest

from requests import Session
from requests_mock import Adapter
from testfixtures import LogCapture
from pkg_resources import resource_string
from parsers import HOPS


class TestHOPS(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)

    def test_fetch_production_ok(self):
        response_text = resource_string("parsers.test.mocks", "hops.json")
        self.adapter.register_uri("GET", "https://www.hops.hr/Home/PowerExchange", content=response_text)
        response_text = resource_string("parsers.test.mocks", "hrote_dates.json")
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/dates.json",
                                  content=response_text)
        response_text = resource_string("parsers.test.mocks", "hrote.json")
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/"
                                         "28.9.2019.json", content=response_text)

        data = HOPS.fetch_production('HR', self.session)
        self.assertIsNotNone(data)
        data = data[0]
        self.assertEqual(data['zoneKey'], 'HR')
        self.assertEqual(data['source'], 'hops.hr')
        self.assertIsNotNone(data['datetime'])
        self.assertIsNotNone(data['production'])
        self.assertEqual(data['production']['wind'], 3.0)
        self.assertEqual(data['production']['solar'], 15.34333)
        self.assertEqual(data['production']['unknown'], 898.65667)

    def test_fetch_production_no_solar(self):
        response_text = resource_string("parsers.test.mocks", "hops.json")
        self.adapter.register_uri("GET", "https://www.hops.hr/Home/PowerExchange", content=response_text)
        response_text = resource_string("parsers.test.mocks", "hrote_dates.json")
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/dates.json",
                                  content=response_text)
        response_text = resource_string("parsers.test.mocks", "hrote_no_solar_on_that_hour.json")
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/"
                                         "28.9.2019.json", content=response_text)

        with LogCapture() as log:
            data = HOPS.fetch_production('HR', self.session)

        self.assertTrue(('parsers.HOPS', 'WARNING', 'No value for Solar power production on '
                                                 '2019-09-28 16:00:00') in log.actual())
        self.assertIsNotNone(data)
        data = data[0]
        self.assertEqual(data['zoneKey'], 'HR')
        self.assertEqual(data['source'], 'hops.hr')
        self.assertIsNotNone(data['datetime'])
        self.assertIsNotNone(data['production'])
        self.assertEqual(data['production']['wind'], 3.0)
        self.assertEqual(data['production']['solar'], None)
        self.assertEqual(data['production']['unknown'], 914.0)


if __name__ == '__main__':
    unittest.main()
