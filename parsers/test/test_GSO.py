from pathlib import Path

from requests import Session
from requests_mock import POST, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers import GSO

base_path_to_mock = Path("parsers/test/mocks/GSO")


class TestGSO(TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)


class TestFetchProduction(TestGSO):
    def test_production_with_snapshot(self):
        raw_data = Path(base_path_to_mock, "currentGen.json")
        self.adapter.register_uri(
            POST,
            "https://www.gso.org.my/SystemData/CurrentGen.aspx/GetChartDataSource",
            content=raw_data.read_bytes(),
        )
        production = GSO.fetch_production(ZoneKey("MY-WM"), self.session)

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


class TestFetchConsumption(TestGSO):
    def test_consumption_with_snapshot(self):
        raw_data = Path(base_path_to_mock, "systemDemand.json")
        self.adapter.register_uri(
            POST,
            "https://www.gso.org.my/SystemData/SystemDemand.aspx/GetChartDataSource",
            content=raw_data.read_bytes(),
        )
        consumption = GSO.fetch_consumption(ZoneKey("MY-WM"), self.session)

        self.assert_match_snapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "zoneKey": element["zoneKey"],
                    "consumption": element["consumption"],
                }
                for element in consumption
            ]
        )
