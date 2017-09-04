import unittest

from requests import Session
from parsers import ES_IB
from mock import patch
from reescraper import BalearicIslands
from parsers.lib.exceptions import ParserException


class TestESIB(unittest.TestCase):

    def setUp(self):
        self.session = Session()

    @patch.object(BalearicIslands, 'get_all')
    def test_fetch_consumption(self, mocked_get_all):
        mocked_get_all.return_value = []
        try:
            data_list = ES_IB.fetch_consumption('ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['countryCode'], 'ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['datetime'])
                self.assertIsNotNone(data['consumption'])
        except ParserException as ex:
            self.assertIsNotNone(ex)
            self.assertIsInstance(ex, ParserException)
        except Exception as ex:
            self.fail(ex.message)

    def test_fetch_production(self):
        try:
            data_list = ES_IB.fetch_production('ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['countryCode'], 'ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['datetime'])
                self.assertIsNotNone(data['production'])
                self.assertIsNotNone(data['storage'])
        except ParserException as ex:
            self.assertIsNotNone(ex)
            self.assertIsInstance(ex, ParserException)
        except Exception as ex:
            self.fail(ex.message)

    def test_fetch_exchange(self):
        try:
            data_list = ES_IB.fetch_exchange('ES', 'ES-IB', self.session)
            self.assertIsNotNone(data_list)
            for data in data_list:
                self.assertEqual(data['sortedCountryCodes'], 'ES->ES-IB')
                self.assertEqual(data['source'], 'demanda.ree.es')
                self.assertIsNotNone(data['netFlow'])
                self.assertIsNotNone(data['datetime'])
        except ParserException as ex:
            self.assertIsNotNone(ex)
            self.assertIsInstance(ex, ParserException)
        except Exception as ex:
            self.fail(ex.message)

if __name__ == '__main__':
    unittest.main()
