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
