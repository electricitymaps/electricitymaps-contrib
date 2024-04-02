from datetime import datetime
from unittest import TestCase
from zoneinfo import ZoneInfo

import freezegun
from requests import Session
from requests_mock import ANY, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers.CENACE import fetch_consumption


class TestFetchConsumption(TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        with open("parsers/test/mocks/CENACE/DemandaRegional.html", "rb") as data:
            self.adapter.register_uri(ANY, ANY, content=data.read())

    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_fetch_consumption_MX_OC(self):
        data = fetch_consumption(ZoneKey("MX-OC"), self.session)
        assert data[0]["zoneKey"] == "MX-OC"
        assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Mexico_City"))
        assert data[0]["consumption"] == 8519.0

    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_fetch_consumption_MX_BC(self):
        data = fetch_consumption(ZoneKey("MX-BC"), self.session)
        assert data[0]["zoneKey"] == "MX-BC"
        assert data[0]["datetime"] == datetime.now(ZoneInfo("America/Tijuana"))
        assert data[0]["consumption"] == 1587.0

    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_fetch_consumption_BCS(self):
        data = fetch_consumption(ZoneKey("MX-BCS"), self.session)
        assert len(data) == 0
