from validators.zone_specific_checks import (
    validate_hydro_production_is_possible,
    validate_production_has_fossil_fuel,
)

from .lib.fixtures import load_fixture


def test_validate_production_has_fossil_fuel():
    events = load_fixture("production_with_no_fossil_fuel")
    res = validate_production_has_fossil_fuel(events)
    assert res["2022-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 01:00:00+00:00"] == 0
    assert res["2022-01-01 02:00:00+00:00"] == 1


def test_validate_hydro_production_is_possible():
    events = load_fixture("US-CAR-YAD_production_with_invalid_hydro")
    res = validate_hydro_production_is_possible(events)
    assert res["2022-01-01 00:00:00+00:00"] == 0
    assert res["2022-01-01 01:00:00+00:00"] == 1
