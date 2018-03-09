import unittest
from json import loads

from pkg_resources import resource_string
from requests import Session

from parsers import ESIOS
from requests_mock import ANY, Adapter


class TestESIOS(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)

    def test_fetch_exchange(self):
        json_data = resource_string("parsers.test.mocks", "ESIOS_ES_MA.json")
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
