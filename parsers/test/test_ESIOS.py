import unittest
from json import loads
from pathlib import Path

from requests import Session
from requests_mock import ANY, Adapter

from parsers import ESIOS

MOCK_DIR = Path(__file__).parent / 'mocks'


class TestESIOS(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)

    def test_fetch_exchange(self):
        with Path(MOCK_DIR, "ESIOS_ES_MA.json").open('rb') as f:
            json_data = f.read()
        self.adapter.register_uri(ANY, ANY, json=loads(json_data.decode("utf-8")))
        try:
            data_list = ESIOS.fetch_exchange('ES', 'MA', self.session, 'ESIOS_MOCK_TOKEN')
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['sortedZoneKeys'], 'ES->MA')
                self.assertEqual(data['source'], 'api.esios.ree.es')
                self.assertIsNotNone(data['datetime'])
                self.assertIsNotNone(data['netFlow'])
        except Exception as ex:
            self.fail(ex.message)


if __name__ == '__main__':
    unittest.main()
