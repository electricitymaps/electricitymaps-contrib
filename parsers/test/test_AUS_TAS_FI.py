#!/usr/bin/env python3

import json
import unittest
from unittest.mock import patch

from pkg_resources import resource_string
from requests import Session
from requests_mock import Adapter
from testfixtures import LogCapture

from parsers import ajenti


class TestAusTasKi(unittest.TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_parsing_payload(self):
        filename = "parsers/test/mocks/AUS_TAS_FI_payload1.json"
        with open(filename) as f:
            fake_data = json.load(f)
        with patch("parsers.ajenti.SignalR.get_value") as f:
            f.return_value = fake_data
            data = ajenti.fetch_production()

        self.assertIsNotNone(data["production"])
        self.assertEqual(data["production"]["wind"], 0.595)
        self.assertEqual(data["production"]["solar"], 0.004)
        self.assertEqual(data["production"]["oil"], 0.283)
        self.assertEqual(data["production"]["biomass"], 0)


if __name__ == "__main__":
    unittest.main()
