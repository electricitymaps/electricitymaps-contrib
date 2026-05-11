import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from electricitymap.contrib.parsers.lib.nordpool_intraday_schemas import (
    ContractStatisticsResponse,
)

FIXTURE = Path(__file__).parent / "fixtures" / "stats_ger_2026-05-09.json"


def test_real_payload_validates() -> None:
    payload = json.loads(FIXTURE.read_text())
    parsed = ContractStatisticsResponse.parse_obj(payload)
    assert len(parsed.__root__) == 1
    assert parsed.__root__[0].deliveryArea == "GER"
    assert len(parsed.__root__[0].contracts) >= 300


def test_unknown_field_raises_drift_alert() -> None:
    payload = json.loads(FIXTURE.read_text())
    payload[0]["contracts"][0]["_drift_field_"] = "should-fail"
    with pytest.raises(ValidationError) as excinfo:
        ContractStatisticsResponse.parse_obj(payload)
    assert any("_drift_field_" in str(err) for err in excinfo.value.errors())


# ---------------------------------------------------------------------------
# Tests for fetch_intraday_contract_statistics (Task 3)
# ---------------------------------------------------------------------------


def _stub_session(payload):
    """Build a mock session and pre-populate the module-level token cache."""
    from datetime import datetime, timezone
    from unittest.mock import MagicMock

    import electricitymap.contrib.parsers.NORDPOOL as nordpool_mod
    from electricitymap.contrib.parsers.NORDPOOL import NordpoolToken

    session = MagicMock()
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    session.get.return_value = response

    nordpool_mod.CURRENT_TOKEN = NordpoolToken(
        token="fake",
        expiration=datetime(2099, 1, 1, tzinfo=timezone.utc),
    )
    return session


def test_fetch_intraday_contract_statistics_happy_path() -> None:
    """Returns (raw_payload, parsed, None) on a valid payload."""
    from datetime import date

    from electricitymap.contrib.parsers.NORDPOOL import (
        IntradayContractStatisticsResult,
        fetch_intraday_contract_statistics,
    )

    payload = json.loads(FIXTURE.read_text())
    session = _stub_session(payload)

    result = fetch_intraday_contract_statistics(
        area="GER",
        delivery_date=date(2026, 5, 9),
        session=session,
    )

    assert isinstance(result, IntradayContractStatisticsResult)
    assert result.raw == payload
    assert result.parsed is not None
    # NOTE: pydantic v1 uses __root__, not .root
    assert result.parsed.__root__[0].deliveryArea == "GER"
    assert result.errors is None
    call = session.get.call_args
    assert "Intraday/ContractStatistics/ByAreas" in call[0][0]
    assert call[1]["params"]["areas"] == "GER"
    assert call[1]["params"]["date"] == "2026-05-09"


def test_fetch_intraday_contract_statistics_drift() -> None:
    """On drift, returns (raw, None, errors) — does NOT raise. The bronze layer
    needs the raw payload landed even on drift."""
    from datetime import date

    from electricitymap.contrib.parsers.NORDPOOL import (
        fetch_intraday_contract_statistics,
    )

    drifted_payload = json.loads(FIXTURE.read_text())
    drifted_payload[0]["contracts"][0]["_drift_field_"] = "boom"
    session = _stub_session(drifted_payload)

    result = fetch_intraday_contract_statistics(
        area="GER",
        delivery_date=date(2026, 5, 9),
        session=session,
    )

    assert result.raw == drifted_payload
    assert result.parsed is None
    assert result.errors is not None
    assert any("_drift_field_" in str(e) for e in result.errors)
