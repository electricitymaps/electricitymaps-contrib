import os
import unittest
from datetime import datetime

from pytz import utc
from requests import Session
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENTSOE
from electricitymap.contrib.lib.models.events import EventSourceType


class TestENTSOE(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ["ENTSOE_TOKEN"] = "token"
        self.session = Session()
        self.adapter = Adapter()
        self.session.mount("https://", self.adapter)


class TestFetchPrices(TestENTSOE):
    def test_fetch_prices(self):
        with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
            self.adapter.register_uri(
                GET,
                ANY,
                content=price_fr_data.read(),
            )
            prices = ENTSOE.fetch_price(ZoneKey("FR"), self.session)
            self.assertEqual(len(prices), 48)
            self.assertEqual(prices[0]["price"], 106.78)
            self.assertEqual(prices[0]["source"], "entsoe.eu")
            self.assertEqual(prices[0]["currency"], "EUR")
            self.assertEqual(
                prices[0]["datetime"], datetime(2023, 5, 6, 22, 0, tzinfo=utc)
            )

    def test_fetch_prices_integrated_zone(self):
        with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
            self.adapter.register_uri(
                GET,
                ANY,
                content=price_fr_data.read(),
            )
            prices = ENTSOE.fetch_price(ZoneKey("DK-BHM"), self.session)
            self.assertEqual(len(prices), 48)
            self.assertEqual(prices[0]["price"], 106.78)
            self.assertEqual(prices[0]["source"], "entsoe.eu")
            self.assertEqual(prices[0]["currency"], "EUR")
            self.assertEqual(
                prices[0]["datetime"], datetime(2023, 5, 6, 22, 0, tzinfo=utc)
            )


class TestFetchExchange(TestENTSOE):
    def test_fetch_exchange(self):
        with open(
            "parsers/test/mocks/ENTSOE/FR_DE_exchange.xml", "rb"
        ) as exchange_fr_de_data:
            self.adapter.register_uri(
                GET,
                ANY,
                content=exchange_fr_de_data.read(),
            )
            exchanges = ENTSOE.fetch_exchange(
                ZoneKey("FR"), ZoneKey("DE"), self.session
            )
            self.assertEqual(len(exchanges), 47)
            self.assertEqual(exchanges[0]["netFlow"], -0.0)
            self.assertEqual(exchanges[0]["source"], "entsoe.eu")
            self.assertEqual(
                exchanges[0]["datetime"], datetime(2023, 5, 6, 22, 0, tzinfo=utc)
            )
            self.assertEqual(exchanges[0]["sourceType"], EventSourceType.measured)

    def test_fetch_exchange_integrated_zone(self):
        with open(
            "parsers/test/mocks/ENTSOE/FR_DE_exchange.xml", "rb"
        ) as exchange_fr_de_data:
            self.adapter.register_uri(
                GET,
                ANY,
                content=exchange_fr_de_data.read(),
            )
            exchanges = ENTSOE.fetch_exchange(
                ZoneKey("DE"), ZoneKey("FR"), self.session
            )
            self.assertEqual(len(exchanges), 47)
            self.assertEqual(exchanges[0]["netFlow"], -0.0)
            self.assertEqual(exchanges[0]["source"], "entsoe.eu")
            self.assertEqual(
                exchanges[0]["datetime"], datetime(2023, 5, 6, 22, 0, tzinfo=utc)
            )
            self.assertEqual(exchanges[0]["sourceType"], EventSourceType.measured)


class TestFetchForecastedExchanges(TestENTSOE):
    def test_fetch_forecasted_exchanges(self):
        with open(
            "parsers/test/mocks/ENTSOE/FR_DE_exchange.xml", "rb"
        ) as exchange_fr_de_data:
            self.adapter.register_uri(
                GET,
                ANY,
                content=exchange_fr_de_data.read(),
            )
            exchanges = ENTSOE.fetch_exchange_forecast(
                ZoneKey("FR"), ZoneKey("DE"), self.session
            )
            self.assertEqual(len(exchanges), 47)
            self.assertEqual(exchanges[0]["netFlow"], -0.0)
            self.assertEqual(exchanges[0]["source"], "entsoe.eu")
            self.assertEqual(
                exchanges[0]["datetime"], datetime(2023, 5, 6, 22, 0, tzinfo=utc)
            )
            self.assertEqual(exchanges[0]["sourceType"], EventSourceType.forecasted)
