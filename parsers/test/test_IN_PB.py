import unittest

from requests import Session
from requests_mock import Adapter
from pkg_resources import resource_string
from parsers import IN_PB


class TestINPB(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('http://', self.adapter)

    def test_fetch_consumption(self):
        response_text = resource_string("parsers.test.mocks", "IN_PB_nrGenReal.html")
        self.adapter.register_uri("GET", "http://www.punjabsldc.org/nrrealw.asp?pg=nrGenReal",
                                  content=response_text)
        try:
            data = IN_PB.fetch_consumption('IN-PB', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'IN-PB')
            self.assertEqual(data['source'], 'punjasldc.org')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['consumption'])
            self.assertEqual(data['consumption'], 7451.0)
        except Exception as ex:
            self.fail("IN_KA.fetch_consumption() raised Exception: {0}".format(ex.message))

    def test_fetch_production(self):
        response_text = resource_string("parsers.test.mocks", "IN_PB_pbGenReal.html")
        self.adapter.register_uri("GET", "http://www.punjabsldc.org/pungenrealw.asp?pg=pbGenReal",
                                  content=response_text)
        try:
            data = IN_PB.fetch_production('IN-PB', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['countryCode'], 'IN-PB')
            self.assertEqual(data['source'], 'punjasldc.org')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['production'])
            self.assertEqual(data['production']['hydro'], 554.0)
            self.assertIsNotNone(data['storage'])
        except Exception as ex:
            self.fail("IN_KA.fetch_production() raised Exception: {0}".format(ex.message))


if __name__ == '__main__':
    unittest.main()
