from datetime import datetime, timedelta, timezone
from importlib import resources

from freezegun import freeze_time
from requests import Session
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from parsers.lib.exceptions import ParserException
from parsers.PF import fetch_production


class TestPF(TestCase):
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
            text=resources.files("parsers.test.mocks.PF")
            .joinpath("production_live.html")
            .read_text(),
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

    def test_fetch_production_raises_parser_exception_on_historical_data(self):
        """That a ParserException is raised if requesting historical data (not supported yet)."""
        self.adapter.register_uri(GET, ANY, json=[])

        with self.assertRaisesRegex(
            ParserException,
            expected_regex="This parser is not yet able to parse historical data",
        ):
            historical_datetime = datetime.now(timezone.utc) - timedelta(days=1)
            fetch_production(target_datetime=historical_datetime, session=self.session)
