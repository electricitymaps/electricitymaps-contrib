from pathlib import Path

from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENERCAL

base_path_to_mock = Path("parsers/test/mocks/ENERCAL")


class TestENERCAL(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)


class TestFetchProduction(TestENERCAL):
    def test_production_with_snapshot(self):
        raw_data = Path(base_path_to_mock, "production.json")
        self.adapter.register_uri(
            GET,
            ANY,
            content=raw_data.read_bytes(),
        )
        production = ENERCAL.fetch_production(ZoneKey("NC"), self.session)

        self.assert_match_snapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "production": element["production"],
                    "storage": element["storage"],
                    "source": element["source"],
                    "sourceType": element["sourceType"].value,
                    "correctedModes": element["correctedModes"],
                }
                for element in production
            ]
        )
