import unittest
from pathlib import Path

from requests import Session
from requests_mock import Adapter

from parsers import IN_KA

MOCK_DIR = Path(__file__).parent / 'mocks'

class Test_IN_KA(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('http://', self.adapter)

    def test_fetch_consumption(self):
        with Path(MOCK_DIR, "IN_KA_Default.html").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "http://kptclsldc.com/Default.aspx", content=response_text)

        try:
            data = IN_KA.fetch_consumption('IN-KA', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['zoneKey'], 'IN-KA')
            self.assertEqual(data['source'], 'kptclsldc.com')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['consumption'])
            self.assertEqual(data['consumption'], 7430.0)
        except Exception as ex:
            self.fail("IN_KA.fetch_consumption() raised Exception: {0}".format(ex.message))

    def test_fetch_production(self):
        with Path(MOCK_DIR, "IN_KA_StateGen.html").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "http://kptclsldc.com/StateGen.aspx", content=response_text)
        with Path(MOCK_DIR, "IN_KA_StateNCEP.html").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri("GET", "http://kptclsldc.com/StateNCEP.aspx", content=response_text)

        try:
            data = IN_KA.fetch_production('IN-KA', self.session)
            self.assertIsNotNone(data)
            self.assertEqual(data['zoneKey'], 'IN-KA')
            self.assertEqual(data['source'], 'kptclsldc.com')
            self.assertIsNotNone(data['datetime'])
            self.assertIsNotNone(data['production'])
            self.assertEqual(data['production']['hydro'], 1108.0)
            self.assertIsNotNone(data['storage'])
        except Exception as ex:
            self.fail("IN_KA.fetch_production() raised Exception: {0}".format(ex.message))


if __name__ == '__main__':
    unittest.main()
