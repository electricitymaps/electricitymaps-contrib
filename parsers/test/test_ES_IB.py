import unittest

from requests import Session
from parsers import ES_IB
from mock import patch
from ree import BalearicIslands
from ree import Response


class TestESIB(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        first_request = Response(1504603773)
        first_request.link['pe_ma'] = 50
        second_request = Response(1504603842)
        second_request.link['pe_ma'] = 50
        self.mocked_responses = [first_request, second_request]

    @patch.object(BalearicIslands, 'get_all')
    def test_fetch_consumption(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        try:
            data_list = ES_IB.fetch_consumption('ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['zoneKey'], 'ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['datetime'])
                self.assertIsNotNone(data['consumption'])
        except Exception as ex:
            self.fail(ex.message)

    @patch.object(BalearicIslands, 'get_all')
    def test_fetch_production(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        try:
            data_list = ES_IB.fetch_production('ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['zoneKey'], 'ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['datetime'])
                self.assertIsNotNone(data['production'])
                self.assertIsNotNone(data['storage'])
        except Exception as ex:
            self.fail(ex.message)

    @patch.object(BalearicIslands, 'get_all')
    def test_fetch_exchange(self, mocked_get_all):
        mocked_get_all.return_value = self.mocked_responses
        try:
            data_list = ES_IB.fetch_exchange('ES', 'ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['sortedZoneKeys'], 'ES->ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['netFlow'])
                self.assertEqual(data['netFlow'], 50.0)
                self.assertIsNotNone(data['datetime'])
        except Exception as ex:
            self.fail(ex.message)

if __name__ == '__main__':
    unittest.main()
