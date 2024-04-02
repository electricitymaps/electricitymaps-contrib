import json
from datetime import datetime, timedelta, timezone
from importlib import resources

from freezegun import freeze_time
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from parsers.CR import fetch_exchange, fetch_production
from parsers.lib.exceptions import ParserException


class TestCR(TestCase):
    def setUp(self) -> None:
        super().setUp()

        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

    @freeze_time("2024-01-01 12:00:00")
    def test_fetch_production_live(self):
        """That we can fetch the production mix at the current time."""
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.CR")
                .joinpath("production_live.json")
                .read_text()
            ),
        )

        production = fetch_production(session=self.session)

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

    def test_fetch_production_historical(self):
        """That we can fetch historical energy production values."""
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.CR")
                .joinpath("production_20210716.json")
                .read_text()
            ),
        )

        historical_datetime = datetime(2021, 7, 16, 16, 20, 30, tzinfo=timezone.utc)
        production_breakdowns = fetch_production(
            target_datetime=historical_datetime.astimezone(timezone.utc),
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
                for element in production_breakdowns
            ]
        )

    @freeze_time("2024-01-01 12:00:00")
    def test_fetch_exchange_live(self):
        """That we can fetch the last known power exchanges."""
        self.adapter.register_uri(
            GET,
            ANY,
            json=json.loads(
                resources.files("parsers.test.mocks.CR")
                .joinpath("exchange_live.json")
                .read_text()
            ),
        )

        exchanges = fetch_exchange(session=self.session)

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "sortedZoneKeys": element["sortedZoneKeys"],
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sourceType": element["sourceType"].value,
                }
                for element in exchanges
            ]
        )

    def test_fetch_exchange_raises_parser_exception_on_historical_data(self):
        """That a ParserException is raised if requesting historical data (not supported yet)."""
        self.adapter.register_uri(GET, ANY, json=[])

        with self.assertRaisesRegex(
            ParserException,
            expected_regex="This parser is not yet able to parse historical data",
        ):
            historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
            fetch_exchange(target_datetime=historical_datetime, session=self.session)
