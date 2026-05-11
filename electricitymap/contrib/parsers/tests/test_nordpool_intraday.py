import copy
import json
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

import electricitymap.contrib.parsers.NORDPOOL as nordpool_mod
from electricitymap.contrib.parsers.lib.nordpool_intraday_schemas import (
    ContractStatisticsResponse,
)
from electricitymap.contrib.parsers.NORDPOOL import (
    IntradayContractStatisticsResult,
    fetch_intraday_contract_statistics,
)

FIXTURE = Path(__file__).parent / "fixtures" / "stats_ger_2026-05-09.json"


@pytest.fixture(scope="session")
def real_payload():
    return json.loads(FIXTURE.read_text())


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


def test_fetch_intraday_contract_statistics_happy_path(real_payload) -> None:
    payload = copy.deepcopy(real_payload)
    session = _stub_session(payload)

    result = fetch_intraday_contract_statistics(
        area="GER",
        delivery_date=date(2026, 5, 9),
        session=session,
    )

    assert isinstance(result, IntradayContractStatisticsResult)
    assert result.raw == payload
    assert result.parsed is not None
    # pydantic v1 uses __root__, not .root
    assert result.parsed.__root__[0].deliveryArea == "GER"
    assert result.errors is None
    call = session.get.call_args
    assert "Intraday/ContractStatistics/ByAreas" in call[0][0]
    assert call[1]["params"]["areas"] == "GER"
    assert call[1]["params"]["date"] == "2026-05-09"


def test_fetch_intraday_contract_statistics_drift(real_payload) -> None:
    """On drift, returns (raw, None, errors). Bronze still lands the raw payload."""
    drifted_payload = copy.deepcopy(real_payload)
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
