import unittest

from electricitymap.contrib.hooks.arrows import filterExchanges


class TestFilterExchanges(unittest.TestCase):
    def test_filter_exchanges_with_aggregated_france(self):
        # Mock exchanges data
        exchanges = {
            "FR": {"netFlow": 100, "co2intensity": 50},
            "DE": {"netFlow": 200, "co2intensity": 30},
        }

        exclusionArrayZones = []
        exclusionArrayCountries = []

        # Call the filterExchanges function
        resultZones, resultCountries = filterExchanges(
            exchanges, exclusionArrayZones, exclusionArrayCountries
        )

        # Assert that the aggregated France data is included in the country view
        self.assertIn("FR", resultCountries)
        self.assertEqual(resultCountries["FR"]["netFlow"], 100)
        self.assertEqual(resultCountries["FR"]["co2intensity"], 50)

    def test_filter_exchanges_exclusion(self):
        # Mock exchanges data
        exchanges = {
            "FR": {"netFlow": 100, "co2intensity": 50},
            "DE": {"netFlow": 200, "co2intensity": 30},
        }

        exclusionArrayZones = ["DE"]
        exclusionArrayCountries = []

        # Call the filterExchanges function
        resultZones, resultCountries = filterExchanges(
            exchanges, exclusionArrayZones, exclusionArrayCountries
        )

        # Assert that 'DE' is excluded from the zone view
        self.assertNotIn("DE", resultZones)
        self.assertIn("FR", resultZones)


if __name__ == "__main__":
    unittest.main()
