import os
import unittest
from datetime import datetime
from unittest import mock

from pytz import utc
from requests import Session
from requests_mock import ANY, GET, Adapter

from electricitymap.contrib.lib.types import ZoneKey
from parsers import ENTSOE
from parsers.lib.utils import get_token


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


class TestENTSOE_Refetch(unittest.TestCase):
    def test_refetch_token(self) -> None:
        token = mock.Mock(return_value="token")
        with mock.patch("parsers.ENTSOE.get_token", token) as patched_get_token:
            self.session = Session()
            self.adapter = Adapter()
            self.session.mount("https://", self.adapter)
            with open("parsers/test/mocks/ENTSOE/FR_prices.xml", "rb") as price_fr_data:
                self.adapter.register_uri(
                    GET,
                    ANY,
                    content=price_fr_data.read(),
                )
                _ = ENTSOE.fetch_price(ZoneKey("DE"), self.session)
                patched_get_token.assert_called_once_with("ENTSOE_TOKEN")
                patched_get_token.reset_mock()
                _ = ENTSOE.fetch_price(
                    ZoneKey("DE"), self.session, datetime(2021, 1, 1)
                )
                patched_get_token.assert_called_once_with("ENTSOE_REFETCH_TOKEN")
