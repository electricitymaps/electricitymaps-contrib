import unittest
from datetime import datetime, timezone

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.libs.models.datapoints import Exchange


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

    def test_raises_if_not_exchange(self):

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