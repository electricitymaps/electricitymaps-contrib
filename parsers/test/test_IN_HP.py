import re
import unittest
from pathlib import Path

from requests import Session
from requests_mock import ANY, Adapter
from testfixtures import LogCapture

from parsers import IN_HP

MOCK_DIR = Path(__file__).parent / 'mocks'

class Test_IN_HP(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)
        with Path(MOCK_DIR, "IN_HP.html").open('rb') as f:
            response_text = f.read()
        self.adapter.register_uri(
            "GET", IN_HP.DATA_URL, text=str(response_text))

    def test_fetch_production(self):
        try:
            with LogCapture() as log:
                data = IN_HP.fetch_production('IN-HP', self.session)
                self.assertEqual(data['zoneKey'], 'IN-HP')
                self.assertEqual(data['source'], 'hpsldc.com')
                self.assertIsNotNone(data['datetime'])
                self.assertEqual(data['production'], {
                    'hydro': 360.42, 'unknown': 115.4})
                # Check rows that failed to parse in each table were logged correctly.
                logs = log.actual()
                self.assertEqual(len(logs), 2)
                self.assertRegex(logs[0][2], re.compile('UNKNOWN HP PLANT'))
                self.assertRegex(logs[1][2], re.compile('UNKNOWN ISGS PLANT'))
        except Exception as ex:
            self.fail(
                "IN_HP.fetch_production() raised Exception: {0}".format(ex))


if __name__ == '__main__':
    unittest.main()
