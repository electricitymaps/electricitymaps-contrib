from json import loads

from pkg_resources import resource_string
from requests import Session
from requests_mock import GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.BORNHOLM_POWERLAB import LATEST_DATA_URL, fetch_exchange, fetch_production


class TestBornholmPowerlab(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)
        realtime = resource_string(
            "parsers.test.mocks.Bornholm_Powerlab", "latest_data.json"
        )
        self.adapter.register_uri(
            GET,
            LATEST_DATA_URL,
            json=loads(realtime.decode("utf-8")),
        )

    def test_fetch_production(self):
        production = fetch_production(
            zone_key=ZoneKey("DK-BHM"),
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
                    "sourceType": element["sourceType"].value,
                }
                for element in production
            ]
        )

    def test_fetch_exchange(self):
        exchange = fetch_exchange(
            session=self.session,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sortedZoneKeys": element["sortedZoneKeys"],
                    "sourceType": element["sourceType"].value,
                }
                for element in exchange
            ]
        )
