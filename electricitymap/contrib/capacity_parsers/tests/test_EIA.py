from datetime import datetime

import pytest
from requests_mock import ANY, GET

from electricitymap.contrib.capacity_parsers import EIA
from electricitymap.contrib.config import ZoneKey

TARGET_DATETIME = datetime(2026, 7, 1)


@pytest.fixture(autouse=True)
def eia_key_env(monkeypatch):
    monkeypatch.setenv("EIA_KEY", "token")


def _row(technology: str, capacity: str) -> dict:
    return {
        "technology": technology,
        "statusDescription": "Operating",
        "nameplate-capacity-mw": capacity,
    }


def _page(rows: list[dict], total: int) -> dict:
    return {"response": {"total": str(total), "data": rows}}


def test_fetch_production_capacity_reads_every_page(adapter, session, monkeypatch):
    monkeypatch.setattr(EIA, "PAGE_SIZE", 2)
    adapter.register_uri(
        GET,
        ANY,
        [
            {
                "json": _page(
                    [_row("Solar Photovoltaic", "10"), _row("Nuclear", "100")], 3
                )
            },
            {"json": _page([_row("Solar Photovoltaic", "5")], 3)},
        ],
    )

    capacity = EIA.fetch_production_capacity(
        ZoneKey("US-CAL-CISO"), TARGET_DATETIME, session
    )

    assert adapter.call_count == 2
    assert "offset=2" in adapter.request_history[1].url
    assert capacity["solar"]["value"] == 15.0
    assert capacity["nuclear"]["value"] == 100.0


def test_fetch_production_capacity_returns_none_without_data(adapter, session):
    adapter.register_uri(GET, ANY, json=_page([], 0))

    assert (
        EIA.fetch_production_capacity(ZoneKey("US-CAL-CISO"), TARGET_DATETIME, session)
        is None
    )


def test_fetch_production_capacity_raises_on_error_payload(adapter, session):
    adapter.register_uri(GET, ANY, json={"error": "API_KEY_INVALID"})

    with pytest.raises(ValueError, match="API_KEY_INVALID"):
        EIA.fetch_production_capacity(ZoneKey("US-CAL-CISO"), TARGET_DATETIME, session)


def test_fetch_production_capacity_raises_on_http_error(adapter, session):
    adapter.register_uri(GET, ANY, status_code=503)

    with pytest.raises(Exception, match="503"):
        EIA.fetch_production_capacity(ZoneKey("US-CAL-CISO"), TARGET_DATETIME, session)


def test_fetch_production_capacity_for_all_zones_skips_failed_zones(monkeypatch):
    zones = [ZoneKey("US-CAL-CISO"), ZoneKey("US-TEX-ERCO"), ZoneKey("US-NY-NYIS")]
    monkeypatch.setattr(EIA, "US_ZONES", zones)

    def fake_fetch(zone_key, target_datetime, session):
        if zone_key == "US-TEX-ERCO":
            raise ValueError("504 Gateway Time-out")
        if zone_key == "US-NY-NYIS":
            return None
        return {"solar": {"value": 1.0}}

    monkeypatch.setattr(EIA, "fetch_production_capacity", fake_fetch)

    assert EIA.fetch_production_capacity_for_all_zones(TARGET_DATETIME) == {
        "US-CAL-CISO": {"solar": {"value": 1.0}}
    }
