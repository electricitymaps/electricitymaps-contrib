from datetime import datetime, timedelta

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
        mock_file_today = open("parsers/test/mocks/PE/response_20240206.json", "rb")
        mock_file_yesterday = open("parsers/test/mocks/PE/response_20240205.json", "rb")
        self.adapter.register_uri(
            POST,
            API_ENDPOINT,
            response_list=[
                {"content": mock_file_today.read()},
                {"content": mock_file_yesterday.read()},
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
                    "production": element["production"],
                    # "storage": element["storage"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": "measured",
                }
                for element in production
            ]
        )

    @freeze_time("2024-02-06 10:00:00", tz_offset=-5)
    def test_api_requests_are_sent_with_correct_dates(self):
        def format_date(date: datetime):
            return date.strftime("%d/%m/%Y").replace("/", "%2F")

        current_date = datetime.now()

        fetch_production(
            zone_key=ZoneKey("PE"),
            session=self.session,
        )

        assert self.adapter.called
        assert self.adapter.call_count == 2
        today_request_data = self.adapter.request_history[0].text
        assert (
            "fechaInicial={today}&fechaFinal={end_date}".format(
                today=format_date(current_date),
                end_date=format_date(current_date + timedelta(days=1)),
            )
            in today_request_data
        )
        yesterday_request_data = self.adapter.request_history[-1].text
        assert (
            "fechaInicial={yesterday}&fechaFinal={today}".format(
                yesterday=format_date(current_date + timedelta(days=-1)),
                today=format_date(current_date),
            )
            in yesterday_request_data
        )
