from unittest import TestCase

import freezegun
from requests import Session
from requests_mock import ANY, Adapter

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.parsers.MX import fetch_consumption


class TestFetchConsumption(TestCase):
    def setUp(self):
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        data = open("parsers/test/mocks/MX/DemandaRegional.html", "rb")
        self.adapter.register_uri(ANY, ANY, content=data.read())

    @freezegun.freeze_time("2021-01-01 00:00:00")
    def test_fetch_consumption(self):

        data = fetch_consumption(ZoneKey("MX-OC"), self.session)
