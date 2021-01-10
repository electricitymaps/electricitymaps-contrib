import unittest
from pathlib import Path

from requests import Session
from requests_mock import Adapter
from testfixtures import LogCapture

from parsers import HOPS

MOCK_DIR = Path(__file__).parent / 'mocks'

class TestHOPS(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)

    def test_fetch_production_ok(self):
        with Path(MOCK_DIR, "hops.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://www.hops.hr/Home/PowerExchange", content=response_text)
        with Path(MOCK_DIR, "hrote_dates.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/dates.json",
                                  content=response_text)
        with Path(MOCK_DIR, "hrote.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/"
                                         "21.5.2020.json", content=response_text)

        data = HOPS.fetch_production('HR', self.session)
        self.assertIsNotNone(data)
        data = data[0]
        self.assertEqual(data['zoneKey'], 'HR')
        self.assertEqual(data['source'], 'hops.hr')
        self.assertIsNotNone(data['datetime'])
        self.assertIsNotNone(data['production'])
        self.assertEqual(data['production']['wind'], 504.0)
        self.assertEqual(data['production']['solar'], 19.5)
        self.assertEqual(data['production']['unknown'], 1474.5)

    def test_fetch_production_no_solar(self):
        with Path(MOCK_DIR, "hops.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://www.hops.hr/Home/PowerExchange", content=response_text)
        with Path(MOCK_DIR, "hrote_dates.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/dates.json",
                                  content=response_text)
        with Path(MOCK_DIR, "hrote_no_solar_on_that_hour.json").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "https://files.hrote.hr/files/EKO_BG/FORECAST/SOLAR/FTP/TEST_DRIVE/"
                                         "21.5.2020.json", content=response_text)

        with LogCapture() as log:
            data = HOPS.fetch_production('HR', self.session)
        self.assertTrue(('parsers.HOPS', 'WARNING', 'No value for Solar power production on '
                                                 '2020-05-21 18:00:00+02:00') in log.actual())
        self.assertIsNotNone(data)
        data = data[0]
        self.assertEqual(data['zoneKey'], 'HR')
        self.assertEqual(data['source'], 'hops.hr')
        self.assertIsNotNone(data['datetime'])
        self.assertIsNotNone(data['production'])
        self.assertEqual(data['production']['wind'], 504.0)
        self.assertEqual(data['production']['solar'], None)
        self.assertEqual(data['production']['unknown'], 1494.0)


if __name__ == '__main__':
    unittest.main()
