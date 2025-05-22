#!/usr/bin/env python3

import json
from unittest.mock import patch

from parsers import ajenti


def test_parsing_payload():
    filename = "parsers/test/mocks/AU/AU_WA_RI_payload1.json"
    with open(filename) as f:
        fake_data = json.load(f)
    with patch("parsers.ajenti.SignalR.get_value") as f:
        f.return_value = fake_data
        data = ajenti.fetch_production()[0]

    assert data["production"] is not None
    assert data["production"]["wind"] == 0.148
    assert data["production"]["solar"] == 0

    assert data["production"]["oil"] == 0.683

    # there is no biomass on that island
    assert data["production"]["biomass"] == 0
