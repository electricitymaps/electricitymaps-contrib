import pandas as pd

from electricitymap.contrib.validators.sanity_checks import (
    validate_positive_production,
    validate_production_one_non_nan_value,
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
