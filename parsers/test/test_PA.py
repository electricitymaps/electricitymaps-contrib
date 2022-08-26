import unittest

import arrow
import requests
import requests_mock
from freezegun import freeze_time
from pkg_resources import resource_string

from parsers import PA


class TestFetchProduction(unittest.TestCase):
    def setUp(self):
        self.adapter = requests_mock.Adapter()
        self.session = requests.Session()
        self.session.mount("https://", self.adapter)

    @freeze_time("2021-12-30 09:58:40", tz_offset=-5)
    def test_nominal_response_uses_timestamp_from_page(self):
        expected_datetime = arrow.get("2021-12-30T09:58:37-05:00").datetime
        nominal_response = resource_string(
            "parsers.test.mocks", "PA_nominal_generation.html"
        )
        self.adapter.register_uri(
            "GET", PA.PRODUCTION_URL, content=nominal_response, status_code=200
        )
        result = PA.fetch_production(session=self.session)
        self.assertEqual(result["datetime"], expected_datetime)

    @freeze_time("2021-12-30 09:57:47", tz_offset=-5)
    def test_nominal_response_maps_to_electricitymap_fuels(self):
        expected_production = {
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
        }
        nominal_response = resource_string(
            "parsers.test.mocks", "PA_nominal_generation.html"
        )
        self.adapter.register_uri(
            "GET", PA.PRODUCTION_URL, content=nominal_response, status_code=200
        )
        result = PA.fetch_production(session=self.session)
        self.assertEqual(result["production"], expected_production)


if __name__ == "__main__":
    unittest.main()
