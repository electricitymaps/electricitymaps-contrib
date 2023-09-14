from datetime import datetime, timezone

from requests import Session
from requests_mock import GET, POST, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.IEMOP import REPORTS_ADMIN_URL, fetch_production

zone_keys = ["PH-LU", "PH-MI", "PH-VI"]


class TestPH(TestCase):
    def setUp(self) -> None:
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    def test_production(self):
        """
        Reports have been reduced to 14 September 2023 00:00 to 13 September 2023 22:00 for ease
        """
        target_datetime = datetime(2023, 9, 14, 0, 0, tzinfo=timezone.utc)
        list_reports_items = open(
            "parsers/test/mocks/IEMOP/list_reports_items.json", "rb"
        )
        self.adapter.register_uri(
            POST,
            REPORTS_ADMIN_URL,
            content=list_reports_items.read(),
        )
        REPORTS_LINK = "https://www.iemop.ph/market-data/dipc-energy-results-raw/?md_file=L3Zhci93d3cvaHRtbC93cC1jb250ZW50L3VwbG9hZHMvZG93bmxvYWRzL2RhdGEvRElQQ0VSL0RJUENFUl8yMDIzMDkxNDAwMDAuemlw"
        reports_byte_content = open("parsers/test/mocks/IEMOP/reports_content", "rb")
        self.adapter.register_uri(
            GET,
            REPORTS_LINK,
            content=reports_byte_content.read(),
        )
        for zone_key in zone_keys:
            with self.subTest(zone_key):
                production = fetch_production(
                    zone_key=ZoneKey(zone_key),
                    session=self.session,
                    target_datetime=target_datetime,
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
