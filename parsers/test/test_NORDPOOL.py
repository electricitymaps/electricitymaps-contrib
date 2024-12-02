import os
from datetime import datetime
from json import loads
from pathlib import Path

from requests import Session
from requests_mock import GET, POST, Adapter
from snapshottest import TestCase

from electricitymap.contrib.lib.types import ZoneKey
from parsers import NORDPOOL

base_path_to_mock = Path("parsers/test/mocks/NORDPOOL")


class TestNordpool(TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["EMAPS_NORDPOOL_USERNAME"] = "username"
        os.environ["EMAPS_NORDPOOL_PASSWORD"] = "password"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)
        self.session.mount("http://", self.adapter)


class TestNordpoolPrice(TestNordpool):
    def test_price_parser_se(self):
        mock_token = Path(base_path_to_mock, "token.json")
        mock_data_current_day = Path(base_path_to_mock, "se_current_day_price.json")
        mock_data_next_day = Path(base_path_to_mock, "se_next_day_price.json")

        self.adapter.register_uri(
            POST,
            "https://sts.nordpoolgroup.com/connect/token",
            json=loads(mock_token.read_text()),
        )
        self.adapter.register_uri(
            GET,
            "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-08",
            json=loads(mock_data_current_day.read_text()),
        )
        self.adapter.register_uri(
            GET,
            "https://data-api.nordpoolgroup.com/api/v2/Auction/Prices/ByAreas?areas=SE4&currency=EUR&market=DayAhead&date=2024-07-09",
            json=loads(mock_data_next_day.read_text()),
        )

        target_datetime = datetime.fromisoformat("2024-07-08")
        price = NORDPOOL.fetch_price(
            zone_key=ZoneKey("SE-SE4"),
            session=self.session,
            target_datetime=target_datetime,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "price": element["price"],
                    "currency": element["currency"],
                    "source": element["source"],
                    "zoneKey": element["zoneKey"],
                    "sourceType": element["sourceType"].value,
                }
                for element in price
            ]
        )


class TestNordpoolExchange(TestNordpool):
    def test_exchange_parser_fi_se1(self):
        mock_token = Path(base_path_to_mock, "token.json")
        mock_data_current_day = Path(
            base_path_to_mock, "fi_se1_current_day_exchange.json"
        )
        mock_data_previous_day = Path(
            base_path_to_mock, "fi_se1_previous_day_exchange.json"
        )

        self.adapter.register_uri(
            POST,
            "https://sts.nordpoolgroup.com/connect/token",
            json=loads(mock_token.read_text()),
        )
        self.adapter.register_uri(
            GET,
            "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-12-01",
            json=loads(mock_data_current_day.read_text()),
        )
        self.adapter.register_uri(
            GET,
            "https://data-api.nordpoolgroup.com/api/v2/PowerSystem/Exchanges/ByAreas?areas=FI&date=2024-11-30",
            json=loads(mock_data_previous_day.read_text()),
        )

        target_datetime = datetime.fromisoformat("2024-12-01")
        exchange = NORDPOOL.fetch_exchange(
            zone_key1=ZoneKey("FI"),
            zone_key2=ZoneKey("SE-SE1"),
            session=self.session,
            target_datetime=target_datetime,
        )

        self.assertMatchSnapshot(
            [
                {
                    "datetime": element["datetime"].isoformat(),
                    "netFlow": element["netFlow"],
                    "source": element["source"],
                    "sourceType": element["sourceType"].value,
                    "sortedZoneKeys": element["sortedZoneKeys"],
                }
                for element in exchange
            ]
        )
