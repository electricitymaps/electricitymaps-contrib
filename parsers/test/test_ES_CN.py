import unittest

from requests import Session
from parsers import ES_CN
from parsers.lib import ParserException


class TestESIB(unittest.TestCase):

    def setUp(self):
        self.session = Session()

    def test_fetch_consumption(self):
        try:
            data = ES_CN.fetch_consumption('ES-CN', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'ES-CN')
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
            data = ES_CN.fetch_production('ES-CN', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'ES-CN')
            self.assertEqual(data['source'], 'demanda.ree.es')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['production'])
            self.assertIsNotNone(data['storage'])
        except ParserException as ex:
            self.assertIsNotNone(ex)
            self.assertIsInstance(ex, ParserException)
        except Exception as ex:
            self.fail(ex.message)

if __name__ == '__main__':
    unittest.main()
