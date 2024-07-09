import os
from pathlib import Path

from requests import Session
from requests_mock import POST, Adapter
from snapshottest import TestCase

base_path_to_mock = Path("parsers/test/mocks/NORDPOOL")

class TestNordpool(TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["EMAPS_NORDPOOL_USERNAME"] = "username"
        os.environ["EMAPS_NORDPOOL_PASSWORD"] = "password"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)

class TestNordpoolPrice(TestNordpool):
    def test_price_parser_se(self):
        mock_token = "token"
        mock_data_current_day = Path(base_path_to_mock, "se_current_day_price.json")
        mock_data_next_day = Path(base_path_to_mock, "se_next_day_price.json")

        self.adapter.register_uri(POST, "https://sts.nordpoolgroup.com/connect/token", text=mock_token)
