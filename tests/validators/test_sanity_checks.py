import pandas as pd

from electricitymap.contrib.config import EXCHANGES_CONFIG
from electricitymap.contrib.validators.sanity_checks import (
    validate_exchange_netflow_doesnt_exceed_capacity,
    validate_exchange_netflow_is_plausible,
    validate_positive_production,
    validate_production_is_plausible,
    validate_production_one_non_nan_value,
    validate_reasonable_time_exchange,
    validate_reasonable_time_production,
)

from .lib.fixtures import load_fixture


def test_validate_positive_production():
    events = load_fixture("production_negative_values")
    res = validate_positive_production(events)
    assert res["2022-01-01 00:00:00+00:00"] == 1
    assert res["2022-01-01 01:00:00+00:00"] == 0
    assert res["2022-01-01 02:00:00+00:00"] == 1


def test_validate_production_one_non_nan_value():
    events = load_fixture("production_with_no_values")
    res = validate_production_one_non_nan_value(events)
    assert res["2022-01-01 00:00:00+00:00"] == 1
    assert res["2022-01-01 01:00:00+00:00"] == 0
    assert res["2022-01-01 02:00:00+00:00"] == 1


def test_validate_production_is_plausible():
    events = load_fixture("production_with_unplausible_productions")
    res = validate_production_is_plausible(events)
    assert res["2022-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 01:00:00+00:00"] == 1
    assert res["2022-01-01 02:00:00+00:00"] == 1


def test_validate_reasonable_time_production():
    events = load_fixture("production_with_unreasonable_datetimes")
    res = validate_reasonable_time_production(events)
    assert res["1982-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 00:00:00+00:00"] == 1
    assert res["2082-01-01 00:00:00+00:00"] == 0


def test_validate_reasonable_time_exchange():
    events = load_fixture("exchange_with_unreasonable_datetimes")
    res = validate_reasonable_time_exchange(events)
    assert res["1982-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 00:00:00+00:00"] == 1
    assert res["2082-01-01 00:00:00+00:00"] == 0


def test_validate_exchange_netflow_is_plausible():
    events = load_fixture("exchange_with_unplausible_netflows")
    res = validate_exchange_netflow_is_plausible(events)
    assert res["2022-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 01:00:00+00:00"] == 0
    assert res["2022-01-01 02:00:00+00:00"] == 1


def test_validate_exchange_netflow_doesnt_exceed_capacity():
    inv_cap = min(EXCHANGES_CONFIG["DK-DK1->DK-DK2"]["capacity"])
    cap = max(EXCHANGES_CONFIG["DK-DK1->DK-DK2"]["capacity"])

    events = pd.DataFrame([cap, inv_cap, 0, cap * 2, inv_cap * 2], columns=["netFlow"])

    res = validate_exchange_netflow_doesnt_exceed_capacity(events, "DK-DK1->DK-DK2")
    assert (res.values == [1, 1, 1, 0, 0]).all()
