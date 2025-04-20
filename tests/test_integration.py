import unittest
from unittest.mock import patch

import requests


class TestIntegration(unittest.TestCase):
    @patch("subprocess.run")
    def test_api_aggregate_france(self, mock_subprocess):
        """Test the /api/aggregate-france endpoint."""
        # Mock the subprocess call to simulate script execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Aggregated data for France"

        # Simulate a request to the API endpoint
        response = requests.get("http://localhost:3000/api/aggregate-france")

        # Assert the response is successful
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aggregated data for France", response.json().get("output"))

    @patch("web.src.api.getZone.fetch")
    def test_frontend_fetch_aggregated_france(self, mock_fetch):
        """Test frontend fetching aggregated France data."""
        # Mock the API response for the aggregated France data
        mock_fetch.return_value.ok = True
        mock_fetch.return_value.json.return_value = {
            "message": "Script executed successfully",
            "output": "Aggregated data for France",
        }

        # Simulate a frontend request for France data
        from web.src.api.getZone import getZone

        result = getZone("hourly", "FR", False)

        # Assert the result matches the mocked API response
        self.assertEqual(result["message"], "Script executed successfully")
        self.assertEqual(result["output"], "Aggregated data for France")


if __name__ == "__main__":
    unittest.main()
