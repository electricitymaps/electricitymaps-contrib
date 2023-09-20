from json import loads
from freezegun import freeze_time
from datetime import datetime

from pkg_resources import resource_string
from requests import Session
from requests_mock import GET, Adapter, ANY
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.ADME import fetch_production, get_adme_url


class TestADME(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    @freeze_time(datetime(2023, 20, 9, 9, 0, 0))
    def test_fetch_production(self):
        production = resource_string("parsers.test.mocks.ADME", "gpf_6507216_6507231_diezminutal.ods")
        self.adapter.register_uri(
            GET,
            ANY,
            json=loads(production.decode("utf-8")),
        )
        production = fetch_production(
            zone_key=ZoneKey("AW"),
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