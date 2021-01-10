import unittest
from pathlib import Path

from requests import Session
from requests_mock import ANY, Adapter

from parsers import IN_AP

MOCK_DIR = Path(__file__).parent / 'mocks'

class Test_IN_AP(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)
        with Path(MOCK_DIR, "IN_AP.html").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri(ANY, ANY, text=str(response_text))

    def test_fetch_production(self):
        try:
            data = IN_AP.fetch_production('IN-AP', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['zoneKey'], 'IN-AP')
            self.assertEqual(data['source'], 'core.ap.gov.in')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['production'])
            self.assertIsNotNone(data['storage'])
        except Exception as ex:
            self.fail(
                "IN_AP.fetch_production() raised Exception: {0}".format(ex))

    def test_fetch_consumption(self):
        try:
            data = IN_AP.fetch_consumption('IN-AP', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['zoneKey'], 'IN-AP')
            self.assertEqual(data['source'], 'core.ap.gov.in')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['consumption'])
        except Exception as ex:
            self.fail(
                "IN_AP.fetch_consumption() raised Exception: {0}".format(ex))


if __name__ == '__main__':
    unittest.main()
