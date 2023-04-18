import logging
import unittest
from datetime import datetime, timezone

from mock import patch

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.libs.models.datapoints import (
    Consumption,
    ConsumptionList,
    Exchange,
    ExchangeList,
)


class TestExchange(unittest.TestCase):
    def test_create_exchange(self):
        exchange = Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        assert exchange.zoneKey == ZoneKey("AT->DE")
        assert exchange.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert exchange.value == 1
        assert exchange.source == "trust.me"

        exchange = Exchange(
            zoneKey=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=-1,
            source="trust.me",
        )
        assert exchange.value == -1

    def test_exchange_list(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        exchange_list.append(
            zone_key=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        exchange_list.append(
            zone_key=ZoneKey("AT->DE"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            value=1,
            source="trust.me",
        )
        assert len(exchange_list.datapoints) == 2

    def test_raises_if_invalid_exchange(self):
        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT->DE"),
                datetime=datetime(2023, 1, 1),
                value=1,
                source="trust.me",
            )

        # This should raise a ValueError because the zoneKey is not an Exchange
        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("AT-DE"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("UNKNOWN->UNKNOWN"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )

        with self.assertRaises(ValueError):
            Exchange(
                zoneKey=ZoneKey("DE->AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )
    def test_append_to_list_logs_error(self):
        exchange_list = ExchangeList(logging.Logger("test"))
        with patch.object(exchange_list.logger, "error") as mock_error:
            exchange_list.append(
                zone_key=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                value=1,
                source="trust.me",
            )
            mock_error.assert_called_once()

class TestConsumption(unittest.TestCase):
    def test_create_consumption(self):
        consumption = Consumption(
            zoneKey=ZoneKey("DE"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        assert consumption.zoneKey == ZoneKey("DE")
        assert consumption.datetime == datetime(2023, 1, 1, tzinfo=timezone.utc)
        assert consumption.consumption == 1
        assert consumption.source == "trust.me"

    def test_raises_if_invalid_consumption(self):
        with self.assertRaises(ValueError):
            Consumption(
                zoneKey=ZoneKey("ATT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=1,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            Consumption(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1),
                consumption=1,
                source="trust.me",
            )
        with self.assertRaises(ValueError):
            Consumption(
                zoneKey=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )
    def test_consumption_list(self):
        consumption_list = ConsumptionList(logging.Logger("test"))
        consumption_list.append(
            zone_key=ZoneKey("AT"),
            datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        consumption_list.append(
            zone_key=ZoneKey("AT"),
            datetime=datetime(2023, 1, 2, tzinfo=timezone.utc),
            consumption=1,
            source="trust.me",
        )
        assert len(consumption_list.datapoints) == 2

    def test_append_to_list_logs_error(self):
        consumption_list = ConsumptionList(logging.Logger("test"))
        with patch.object(consumption_list.logger, "error") as mock_error:
            consumption_list.append(
                zone_key=ZoneKey("AT"),
                datetime=datetime(2023, 1, 1, tzinfo=timezone.utc),
                consumption=-1,
                source="trust.me",
            )
            mock_error.assert_called_once()