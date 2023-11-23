import unittest
from datetime import datetime
from importlib import resources

import requests
import requests_mock
from freezegun import freeze_time

from parsers import PA


class TestFetchProduction(unittest.TestCase):
    def setUp(self):
        self.adapter = requests_mock.Adapter()
        self.session = requests.Session()
        self.session.mount("https://", self.adapter)

    @freeze_time("2021-12-30 09:58:40", tz_offset=-5)
    def test_nominal_response_uses_timestamp_from_page(self):
        self.adapter.register_uri(
            requests_mock.GET,
            PA.PRODUCTION_URL,
            text=resources.files("parsers.test.mocks")
            .joinpath("PA_nominal_generation.html")
            .read_text(),
            status_code=200,
        )
        result = PA.fetch_production(session=self.session)
        self.assertEqual(
            result["datetime"],
            datetime(2021, 12, 30, 9, 58, 37, tzinfo=PA.TIMEZONE),
        )

    @freeze_time("2021-12-30 09:57:47", tz_offset=-5)
    def test_nominal_response_maps_to_electricitymap_fuels(self):
        self.adapter.register_uri(
            requests_mock.GET,
            PA.PRODUCTION_URL,
            text=resources.files("parsers.test.mocks")
            .joinpath("PA_nominal_generation.html")
            .read_text(),
            status_code=200,
        )
        result = PA.fetch_production(session=self.session)
        self.assertEqual(
            result["production"],
            {
                "biomass": 2.75,
                "coal": 149.6,
                "gas": 355.88,
                "geothermal": 0.0,
                "hydro": 421.84,
                "nuclear": 0.0,
                "oil": 238.19999999999996,
                "solar": 262.76,
                "unknown": 0.0,
                "wind": 115.4,
            },
        )


if __name__ == "__main__":
    unittest.main()
