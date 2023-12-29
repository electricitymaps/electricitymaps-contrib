from importlib import resources
from requests import Session
from requests_mock import GET, Adapter, POST
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ESTADISTICO_UT import fetch_production, DAILY_OPERATION_URL


class TestESTADISTICO_UT(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)
        self.adapter.register_uri(
            GET,
            DAILY_OPERATION_URL,
            text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
                .joinpath("production.html")
                .read_text(),
        )
        self.adapter.register_uri(
            POST,
            DAILY_OPERATION_URL,
            text=resources.files("parsers.test.mocks.ESTADISTICO_UT")
                .joinpath("data.html")
                .read_text(),
        )

    def test_fetch_production(self):
        production = fetch_production(
            zone_key=ZoneKey("SV"),
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                }
                for element in production
            ]
        )
