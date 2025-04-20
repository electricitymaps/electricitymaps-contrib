import unittest
from unittest.mock import patch

from electricitymap.contrib.api.getZone import getZone


class TestGetZone(unittest.TestCase):
    @patch('electricitymap.contrib.api.getZone.fetch')
    def test_get_aggregated_france_data(self, mock_fetch):
        # Mock the response from the API endpoint
        mock_fetch.return_value.ok = True
        mock_fetch.return_value.json.return_value = {
            "message": "Script executed successfully",
            "output": "Aggregated data for France"
        }

        # Call the getZone function with 'FR' as the zoneId
        result = getZone('hourly', 'FR', False)

        # Assert the result matches the mocked response
        self.assertEqual(result["message"], "Script executed successfully")
        self.assertEqual(result["output"], "Aggregated data for France")

    @patch('electricitymap.contrib.api.getZone.fetch')
    def test_get_zone_non_france(self, mock_fetch):
        # Mock the response for a non-France zone
        mock_fetch.return_value.ok = True
        mock_fetch.return_value.json.return_value = {
            "zoneStates": "Some data for another zone"
        }

        # Call the getZone function with a non-France zoneId
        result = getZone('hourly', 'DE', False)

        # Assert the result matches the mocked response
        self.assertEqual(result["zoneStates"], "Some data for another zone")

if __name__ == '__main__':
    unittest.main()if __name__ == '__main__':
    unittest.main()