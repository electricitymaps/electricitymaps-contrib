import logging
import unittest
from datetime import datetime, timezone

from mock import patch

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.libs.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.libs.models.events import ProductionMix


class TestExchangeList(unittest.TestCase):
    def test_exchange_list(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        assert len(exchange_list.events) == 2

    def test_append_to_list_logs_error(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        with patch.object(exchange_list.logger, "error") as mock_error:
            exchange_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestConsumptionList(unittest.TestCase):
    def test_consumption_list(self):
        consumption_list = TotalConsumptionList(logging.Logger("test"))
        consumption_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        consumption_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        assert len(consumption_list.events) == 2

    def test_append_to_list_logs_error(self):
        consumption_list = TotalConsumptionList(logging.Logger("test"))
        with patch.object(consumption_list.logger, "error") as mock_error:
            consumption_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()


class TestPriceList(unittest.TestCase):
    def test_price_list(self):
        price_list = PriceList(logging.Logger("test"))
        price_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            price=1,
            source="trust.me",
            currency="EUR",
        )
        assert len(price_list.events) == 1

    def test_append_to_list_logs_error(self):
        price_list = PriceList(logging.Logger("test"))
        with patch.object(price_list.logger, "error") as mock_error:
            price_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                price=1,
                source="trust.me",
                currency="EURO",
            )
            mock_error.assert_called_once()


class TestProductionBreakdownList(unittest.TestCase):
    def test_production_list(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        production_list.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            source="trust.me",
        )
        assert len(production_list.events) == 1

    def test_production_list_logs_error(self):
        production_list = ProductionBreakdownList(logging.Logger("test"))
        with patch.object(production_list.logger, "error") as mock_error:
            production_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                production=ProductionMix(wind=10),
                source="trust.me",
            )
            mock_error.assert_called_once()
        with patch.object(production_list.logger, "warning") as mock_warning:
            production_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                production=ProductionMix(wind=-10),
                source="trust.me",
            )
            mock_warning.assert_called_once()


class TestTotalProductionList(unittest.TestCase):
    def test_total_production_list(self):
        total_production = TotalProductionList(logging.Logger("test"))
        total_production.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        assert len(total_production.events) == 1
