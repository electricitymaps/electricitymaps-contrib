#!/usr/bin/env python3

import json
from unittest.mock import patch

from electricitymap.contrib.parsers import ajenti


def test_parsing_payload():
    filename = "electricitymap/contrib/parsers/tests/mocks/AU/AU_TAS_FI_payload1.json"
    with open(filename) as f:
        fake_data = json.load(f)
    with patch("electricitymap.contrib.parsers.ajenti.SignalR.get_value") as f:
        f.return_value = fake_data
        data = ajenti.fetch_production()[0]

    assert data["production"] is not None
    assert data["production"]["wind"] == 0.595
    assert data["production"]["solar"] == 0.004
    assert data["production"]["oil"] == 0.283
    assert data["production"]["biomass"] == 0
