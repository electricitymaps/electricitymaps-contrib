from importlib import resources

import requests
from freezegun import freeze_time
from requests_mock import ANY, GET, Adapter
from snapshottest import TestCase

from parsers.PA import fetch_production


class TestPA(TestCase):
    def setUp(self):
        super().setUp()
        self.adapter = Adapter()
        self.session = requests.Session()
        self.session.mount("https://", self.adapter)

    @freeze_time("2021-12-30 09:58:40", tz_offset=-5)
    def test_fetch_production(self):
        self.adapter.register_uri(
            GET,
            ANY,
            text=resources.files("parsers.test.mocks")
            .joinpath("PA_nominal_generation.html")
            .read_text(),
            status_code=200,
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
