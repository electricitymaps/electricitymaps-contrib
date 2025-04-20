import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from parsers.BB import fetch_operational_data, scrape_energy_data


class TestBBParser(unittest.TestCase):
    @patch("parsers.BB.requests.Session")
    def test_fetch_operational_data(self, MockSession):
        mock_session = MockSession.return_value
        mock_session.get.return_value.json.return_value = {
            "data": [
                {
                    "data": {
                        "data": [
                            [
                                "datetime",
                                "24 hr monitored solar production",
                                "24 hr monitored wind production",
                            ],
                            ["2025-04-20T00:00:00", "100", "200"],
                        ]
                    }
                }
            ]
        }

        result = fetch_operational_data(
            zone_key="BB",
            session=mock_session,
            target_datetime=None,
            logger=MagicMock(),
        )

        self.assertEqual(result.iloc[0]["24 hr monitored solar production"], 100)
        self.assertEqual(result.iloc[0]["24 hr monitored wind production"], 200)

    @patch("parsers.BB.requests.get")
    def test_scrape_energy_data(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"""
        <html>
            <div class='graph-container'>
                <h3>Energy Production Data</h3>
                <span class='data-point'>100</span>
                <span class='data-point'>200</span>
            </div>
        </html>
        """

        result = scrape_energy_data()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Energy Production Data")
        self.assertEqual(result[0]["data_points"], ["100", "200"])


if __name__ == "__main__":
    unittest.main()
