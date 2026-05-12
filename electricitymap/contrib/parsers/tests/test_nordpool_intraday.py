import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

import electricitymap.contrib.parsers.NORDPOOL as nordpool_mod
from electricitymap.contrib.parsers.lib.nordpool_intraday_schemas import (
    ContractStatisticsResponse,
)
from electricitymap.contrib.types import ZoneKey

FIXTURE = Path(__file__).parent / "fixtures" / "stats_ger_2026-05-09.json"

_EXPECTED_KEYS = {
    "zoneKey",
    "area",
    "apiUpdatedAt",
    "currency",
    "priceUnitRaw",
    "deliveryStart",
    "deliveryEnd",
    "contractId",
    "contractName",
    "contractOpenTime",
    "contractCloseTime",
    "isLocalContract",
    "vwap",
    "vwap1hBeforeClose",
    "vwap3hBeforeClose",
    "openPrice",
    "closePrice",
    "highPrice",
    "lowPrice",
    "openTradeTime",
    "closeTradeTime",
    "volume",
    "buyVolume",
    "sellVolume",
    "source",
}


@pytest.fixture(scope="session")
def real_payload():
    return json.loads(FIXTURE.read_text())


# ---------------------------------------------------------------------------
# Schema-only tests on the fixture (unchanged from original PR).
# ---------------------------------------------------------------------------


def test_real_payload_validates(real_payload) -> None:
    parsed = ContractStatisticsResponse.parse_obj(real_payload)
    assert len(parsed.__root__) == 1
    assert parsed.__root__[0].deliveryArea == "GER"
    assert len(parsed.__root__[0].contracts) >= 300


def test_unknown_field_raises_drift_alert(real_payload) -> None:
    payload = copy.deepcopy(real_payload)
    payload[0]["contracts"][0]["_drift_field_"] = "should-fail"
    with pytest.raises(ValidationError) as excinfo:
        ContractStatisticsResponse.parse_obj(payload)
    assert any("_drift_field_" in str(err) for err in excinfo.value.errors())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stub_session(payload):
    """Build a mock session and pre-populate the module-level token cache."""
    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    session.get.return_value = response

    nordpool_mod.CURRENT_TOKEN = nordpool_mod.NordpoolToken(
        token="fake",
        expiration=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    return session


# ---------------------------------------------------------------------------
# Happy-path: mock _query_nordpool to return the GER fixture for all 5 areas.
# ---------------------------------------------------------------------------


def test_fetch_intraday_contract_statistics_happy_path(real_payload) -> None:
    """Returns list[dict] with correct camelCase keys for all (area, contract) pairs."""
    payload = copy.deepcopy(real_payload)

    # Patch _query_nordpool so it returns a mock response for every area call.
    mock_response = MagicMock()
    mock_response.json.return_value = payload

    with patch.object(nordpool_mod, "_query_nordpool", return_value=mock_response):
        nordpool_mod.CURRENT_TOKEN = nordpool_mod.NordpoolToken(
            token="fake",
            expiration=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        result = nordpool_mod.fetch_intraday_contract_statistics(
            zone_key=ZoneKey("DE"),
            target_datetime=datetime(2026, 5, 9, 12, 0, tzinfo=timezone.utc),
        )

    assert isinstance(result, list)
    assert len(result) > 0

    first = result[0]
    assert isinstance(first, dict)

    # Exact key set check.
    assert set(first.keys()) == _EXPECTED_KEYS

    # Spot-check known good values from the GER fixture.
    assert first["area"] in nordpool_mod._DE_AREAS
    assert first["source"] == "nordpool"
    assert first["zoneKey"] == "DE"
    assert isinstance(first["deliveryStart"], datetime)
    assert isinstance(first["isLocalContract"], bool)

    # Currency parsed correctly from "EUR/MWh".
    assert first["currency"] == "EUR"
    assert first["priceUnitRaw"] == "EUR/MWh"


# ---------------------------------------------------------------------------
# Drift: ValidationError propagates out of fetch_intraday_contract_statistics.
# ---------------------------------------------------------------------------


def test_fetch_intraday_contract_statistics_drift(real_payload) -> None:
    """Schema drift raises ValidationError (feeder catches and skips the area)."""
    drifted_payload = copy.deepcopy(real_payload)
    drifted_payload[0]["contracts"][0]["_drift_field_"] = "boom"

    mock_response = MagicMock()
    mock_response.json.return_value = drifted_payload

    with patch.object(nordpool_mod, "_query_nordpool", return_value=mock_response):
        nordpool_mod.CURRENT_TOKEN = nordpool_mod.NordpoolToken(
            token="fake",
            expiration=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        with pytest.raises(ValidationError) as excinfo:
            nordpool_mod.fetch_intraday_contract_statistics(
                zone_key=ZoneKey("DE"),
                target_datetime=datetime(2026, 5, 9, 12, 0, tzinfo=timezone.utc),
            )

    assert any("_drift_field_" in str(e) for e in excinfo.value.errors())


# ---------------------------------------------------------------------------
# Unsupported zone raises NotImplementedError.
# ---------------------------------------------------------------------------


def test_fetch_intraday_contract_statistics_unsupported_zone() -> None:
    with pytest.raises(NotImplementedError):
        nordpool_mod.fetch_intraday_contract_statistics(zone_key=ZoneKey("FR"))
