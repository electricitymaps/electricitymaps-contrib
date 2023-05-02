import logging
import unittest
from datetime import datetime, timezone

from mock import patch

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix


class TestExchangeList(unittest.TestCase):
    def test_exchange_list(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        exchange_list.append(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            netFlow=1,
            source="trust.me",
        )
        assert len(exchange_list.events) == 2

    def test_append_to_list_logs_error(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        with patch.object(exchange_list.logger, "error") as mock_error:
            exchange_list.append(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                netFlow=1,
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

    def test_merge_production_list_production_mix_only(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=11, coal=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=12, coal=2),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=21, coal=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=22, coal=2),
            source="trust.me",
        )
        production_list_3 = ProductionBreakdownList(logging.Logger("test"))
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=30),
            source="trust.me",
        )
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=31, coal=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2, production_list_3],
            logging.Logger("test"),
            merge_zone_key=ZoneKey("AT"),
            merge_source="trust.me",
        )
        assert len(merged.events) == 3
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].production.wind == 60
        assert merged.events[0].production.coal is None
        assert merged.events[0].source == "trust.me"
        assert merged.events[0].zoneKey == ZoneKey("AT")
        assert merged.events[0].storage is None

        assert merged.events[1].datetime == datetime(2023, 1, 2, tzinfo=timezone.utc)
        assert merged.events[1].production.wind == 63
        assert merged.events[1].production.coal == 3

        assert merged.events[2].datetime == datetime(2023, 1, 3, tzinfo=timezone.utc)
        assert merged.events[2].production.wind == 34
        assert merged.events[2].production.coal == 4

    def test_merge_production_list(self):
        production_list_1 = ProductionBreakdownList(logging.Logger("test"))
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=10),
            storage=StorageMix(hydro=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=11, coal=1),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_1.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=12, coal=2),
            source="trust.me",
        )
        production_list_2 = ProductionBreakdownList(logging.Logger("test"))
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=20),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=21, coal=1),
            source="trust.me",
        )
        production_list_2.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 3, tzinfo=timezone.utc),
            production=ProductionMix(wind=22, coal=2),
            storage=StorageMix(hydro=1, battery=1),
            source="trust.me",
        )
        production_list_3 = ProductionBreakdownList(logging.Logger("test"))
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            production=ProductionMix(wind=30),
            source="trust.me",
        )
        production_list_3.append(
            zoneKey=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            production=ProductionMix(wind=31, coal=1),
            source="trust.me",
        )
        merged = ProductionBreakdownList.merge_production_breakdowns(
            [production_list_1, production_list_2, production_list_3],
            logging.Logger("test"),
            merge_zone_key=ZoneKey("AT"),
            merge_source="trust.me",
        )
        assert len(merged.events) == 3
        assert merged.events[0].datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert merged.events[0].storage.hydro == 2


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
