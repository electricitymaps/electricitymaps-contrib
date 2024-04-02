from datetime import datetime, timezone
from urllib.parse import urlencode

from freezegun import freeze_time
from requests import Session
from requests_mock import POST, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers.PE import API_ENDPOINT, fetch_production


class TestFetchProduction(TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.session = Session()
        self.session.mount("https://", self.adapter)

        with open("parsers/test/mocks/PE/response_20240205.json", "rb") as mock_file:
            self.adapter.register_uri(
                POST,
                API_ENDPOINT,
                response_list=[
                    {"content": mock_file.read()},
                ],
            )

    def test_snapshot(self):
        production = fetch_production(
            zone_key=ZoneKey("PE"),
            session=self.session,
        )

        self.assertMatchSnapshot(
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

    @freeze_time("2024-02-06 10:00:00", tz_offset=-5)
    def test_api_requests_are_sent_with_correct_dates(self):
        end_date = "06/02/2024"
        yesterday = "05/02/2024"
        expected_today_request_data = urlencode(
            {"fechaInicial": yesterday, "fechaFinal": end_date, "indicador": 0}
        )

        fetch_production(
            zone_key=ZoneKey("PE"),
            session=self.session,
            target_datetime=datetime(2024, 2, 6, 0, 0, 0, tzinfo=timezone.utc),
        )

        self.assertTrue(self.adapter.called)
        actual_today_request_data = self.adapter.request_history[0].text
        self.assertEqual(expected_today_request_data, actual_today_request_data)
