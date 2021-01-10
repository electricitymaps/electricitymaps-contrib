import logging
import unittest
from pathlib import Path

from freezegun import freeze_time
from requests import Session
from requests_mock import Adapter
from testfixtures import LogCapture

from parsers import SG

MOCK_DIR = Path(__file__).parent / 'mocks'

class TestSolar(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger('test')
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)
        with Path(MOCK_DIR, 'SG_ema_gov_sg_solar_map.png').open('rb') as f:
            response_data = f.read()
        self.adapter.register_uri('GET', SG.SOLAR_URL, content=response_data)

    @freeze_time('2020-05-05 21:27:00')
    def test_works_when_nonzero(self):
        with Path(MOCK_DIR, 'SG_ema_gov_sg_solar_map_nonzero.png').open('rb') as f:
            response_data = f.read()
        self.adapter.register_uri('GET', SG.SOLAR_URL, content=response_data)
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 8.53)

    @freeze_time('2020-05-05 19:48:00')
    def test_works_when_zero(self):
        power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)

    @freeze_time('2020-05-05 20:49:00')
    def test_ignore_data_older_than_one_hour(self):
        with LogCapture() as log:
            power = SG.get_solar(self.session, logger=self.logger)
        self.assertIsNone(power)

    @freeze_time('2020-05-05 19:47:00')
    def test_allow_remote_clock_to_be_slightly_ahead(self):
        with LogCapture() as log:
            power = SG.get_solar(self.session, logger=self.logger)
        self.assertEqual(power, 0.0)


if __name__ == '__main__':
    unittest.main()
