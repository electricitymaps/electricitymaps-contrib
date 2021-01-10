#!/usr/bin/env python3

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from requests import Session
from requests_mock import Adapter

from parsers import AUS_TAS_KI

MOCK_DIR = Path(__file__).parent / 'mocks'

class TestAusTasKi(unittest.TestCase):

    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount('https://', self.adapter)

    def test_parsing_payload(self):
        with open(MOCK_DIR / 'AUS_TAS_KI_payload1.json') as f:
            fake_data = json.load(f)
        with patch('parsers.AUS_TAS_KI.SignalR.get_value') as f:
            f.return_value = fake_data
            data = AUS_TAS_KI.fetch_production()

        self.assertIsNotNone(data['production'])
        self.assertEqual(data['production']['wind'], 1.024)
        self.assertEqual(data['production']['solar'], 0)

        self.assertEqual(data['production']['oil'], 0.779)
        self.assertEqual(data['production']['biomass'], 0)

    # This test will fetch the payload from the webservice
    # def test_parsing_payload_real(self):
    #     data = AUS_TAS_KI.fetch_production()

    #     self.assertIsNotNone(data['production'])
    #     self.assertIsNotNone(data['production']['wind'])
    #     self.assertIsNotNone(data['production']['solar'])


if __name__ == '__main__':
    unittest.main()
