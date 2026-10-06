import logging
from datetime import datetime, timezone

import pytest

from electricitymap.contrib.parsers import CH
from electricitymap.contrib.parsers.CH import get_solar_capacity_at


@pytest.mark.parametrize(
    "dt,expected",
    [
        ("2018-01-02", 2107.374),
        ("2022-01-01", 4080.415),
        ("2023-01-01", 5094.375),
        ("2024-01-01", 5108.034),
        # make sure past date for which we do not have historical capacity returns earliest available data
        ("2014-02-01", 1398.217),
        # make sure future date for which we do not have historical capacity returns latest available data
        ("2024-02-01", 5108.034),
    ],
)
def test_get_solar_capacity(dt, expected):
    target_datetime = datetime.fromisoformat(dt).replace(tzinfo=timezone.utc)
    assert get_solar_capacity_at(target_datetime) == expected


T10 = datetime(2024, 3, 12, 10, tzinfo=timezone.utc)
T11 = datetime(2024, 3, 12, 11, tzinfo=timezone.utc)


def _exchange(
    key: str,
    dt: datetime,
    net_flow: float | None,
    exports: float | None = None,
    imports: float | None = None,
) -> dict:
    return {
        "sortedZoneKeys": key,
        "datetime": dt,
        "netFlow": net_flow,
        "exports": exports,
        "imports": imports,
        "source": "entsoe.eu",
    }


def test_fetch_swiss_exchanges_ignores_one_sided_exchanges(monkeypatch):
    exchanges_by_neighbour = {
        "AT": [
            _exchange("AT->CH", T10, 100.0, exports=150.0, imports=50.0),
            _exchange("AT->CH", T11, None, exports=80.0),
        ],
        "DE": [
            _exchange("CH->DE", T10, None, imports=40.0),
            _exchange("CH->DE", T11, -20.0, exports=10.0, imports=30.0),
        ],
        "IT": [],
        "FR": [
            _exchange("CH->FR", T10, 5.0, exports=5.0, imports=0.0),
        ],
    }
    monkeypatch.setattr(
        CH.ENTSOE,
        "fetch_exchange",
        lambda zone_key1, zone_key2, **kwargs: exchanges_by_neighbour[zone_key2],
    )

    transmissions = CH.fetch_swiss_exchanges(
        session=None, target_datetime=T11, logger=logging.getLogger("test")
    )

    assert transmissions == {T10: 105.0, T11: -20.0}


def test_fetch_swiss_exchanges_omits_datetimes_with_only_one_sided_exchanges(
    monkeypatch,
):
    exchanges_by_neighbour = {
        "AT": [_exchange("AT->CH", T10, None, exports=80.0)],
        "DE": [_exchange("CH->DE", T10, None, imports=40.0)],
        "IT": [],
        "FR": [],
    }
    monkeypatch.setattr(
        CH.ENTSOE,
        "fetch_exchange",
        lambda zone_key1, zone_key2, **kwargs: exchanges_by_neighbour[zone_key2],
    )

    transmissions = CH.fetch_swiss_exchanges(
        session=None, target_datetime=T10, logger=logging.getLogger("test")
    )

    assert transmissions == {}
