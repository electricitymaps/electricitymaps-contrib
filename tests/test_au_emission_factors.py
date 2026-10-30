import csv
from dataclasses import replace
from io import StringIO
from pathlib import Path

import pytest

from scripts.au_emission_factors import (
    GENERATION_COLUMN,
    SCOPE_1_COLUMN,
    calculate_factors,
    read_nger,
    write_factors,
)

DATA_DIR = Path(__file__).parents[1] / "notebooks/au_emission_factors"


def facility(**changes):
    return {
        "Reporting entity": "Example operator",
        "Facility name": "Example station",
        "Type": "F",
        "State": "NSW",
        "Grid connected": "On",
        "Grid": "NEM",
        "Primary fuel": "Gas",
        GENERATION_COLUMN: "100",
        SCOPE_1_COLUMN: "40",
        "Total emissions \n(t CO2-e)": "999",
        "Emission intensity \n(t CO2-e/ MWh)": "9.99",
        **changes,
    }


def test_generation_weighted_scope_1_not_mean_or_total_emissions():
    rows = [
        facility(**{GENERATION_COLUMN: "100", SCOPE_1_COLUMN: "20"}),
        facility(**{GENERATION_COLUMN: "900", SCOPE_1_COLUMN: "450"}),
    ]
    (factor,) = calculate_factors(rows)
    assert factor.generation_mwh == 1000
    assert factor.emissions_tco2e == 470
    assert factor.direct_gco2e_per_kwh == 470
    assert factor.reporting_records == 2


@pytest.mark.parametrize(
    "changes, expected",
    [
        ({"State": "ACT"}, "AU-NSW"),
        ({"State": "QLD"}, "AU-QLD"),
        ({"State": "WA", "Grid": "SWIS"}, "AU-WA"),
        ({"State": "NT", "Grid": "DKIS"}, "AU-NT"),
        ({"State": "WA", "Grid": "NWIS"}, None),
        ({"State": "QLD", "Grid": "Mt Isa"}, None),
        ({"State": "NT", "Grid": "Off-grid"}, None),
        ({"State": "WA", "Grid": "NEM"}, None),
        ({"Grid connected": "Off"}, None),
        ({"Type": "C"}, None),
    ],
)
def test_grids_and_subtotals(changes, expected):
    factors = calculate_factors([facility(**changes)])
    assert [factor.zone for factor in factors] == ([expected] if expected else [])


@pytest.mark.parametrize(
    "fuel, mode",
    [
        ("Black Coal", "coal"),
        ("Brown Coal", "coal"),
        ("Gas", "gas"),
        ("Coal Seam Methane", "gas"),
        ("Waste Coal Mine Gas", "gas"),
        ("Ethane", "gas"),
        ("Diesel", "oil"),
        ("Kerosene", "oil"),
    ],
)
def test_fossil_fuels(fuel, mode):
    (factor,) = calculate_factors([facility(**{"Primary fuel": fuel})])
    assert factor.mode == mode


@pytest.mark.parametrize(
    "fuel", ["Solar", "Wind", "Battery", "Hydro", "Bagasse", "Landfill Gas", "Biofuel"]
)
def test_other_modes_keep_their_existing_methodology(fuel):
    assert calculate_factors([facility(**{"Primary fuel": fuel})]) == []


def test_documented_callide_duplicate_is_counted_once():
    first = facility(
        **{
            "Facility name": "Callide C Power Station",
            "Reporting entity": "C S ENERGY LIMITED",
            "Primary fuel": "Black Coal",
            "State": "QLD",
            GENERATION_COLUMN: "1,000",
            SCOPE_1_COLUMN: "900",
        }
    )
    second = {**first, "Reporting entity": "IG POWER HOLDINGS LIMITED"}
    other = {**first, "Facility name": "Other coal station", SCOPE_1_COLUMN: "500"}
    for rows in ([first, second, other], [second, first, other]):
        (factor,) = calculate_factors(rows)
        assert factor.direct_gco2e_per_kwh == 700
        assert factor.reporting_records == 2


def test_callide_conflicting_reports_require_manual_review():
    first = facility(
        **{
            "Facility name": "Callide C Power Station",
            "Reporting entity": "C S ENERGY LIMITED",
        }
    )
    second = {
        **first,
        "Reporting entity": "IG POWER HOLDINGS LIMITED",
        GENERATION_COLUMN: "200",
    }
    with pytest.raises(ValueError, match="review deduplication"):
        calculate_factors([first, second])


def test_same_named_station_reports_are_not_automatically_deduplicated():
    rows = [
        facility(**{"Facility name": "Moranbah Power Station", SCOPE_1_COLUMN: "20"}),
        facility(**{"Facility name": "Moranbah Power Station", SCOPE_1_COLUMN: "50"}),
    ]
    (factor,) = calculate_factors(rows)
    assert factor.generation_mwh == 200
    assert factor.direct_gco2e_per_kwh == 350


def test_zero_generation_is_excluded_without_assigning_a_zero_factor():
    rows = [facility(**{GENERATION_COLUMN: "0", SCOPE_1_COLUMN: "10"}), facility()]
    (factor,) = calculate_factors(rows)
    assert factor.direct_gco2e_per_kwh == 400
    assert factor.reporting_records == 1
    assert calculate_factors(rows[:1]) == []


@pytest.mark.parametrize("column", [GENERATION_COLUMN, SCOPE_1_COLUMN])
@pytest.mark.parametrize("value", ["-1", "NaN", "inf", "-"])
def test_invalid_numeric_values_are_not_silently_accepted(column, value):
    with pytest.raises(ValueError):
        calculate_factors([facility(**{column: value})])


def test_cer_csv_encoding_multiline_headers_and_thousands(tmp_path):
    row = facility(**{"Facility name": "Station – west", GENERATION_COLUMN: "1,000"})
    content = StringIO(newline="")
    writer = csv.DictWriter(content, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    path = tmp_path / "source.csv"
    path.write_bytes(content.getvalue().encode("cp1252"))
    loaded = read_nger(path)
    assert loaded[0]["Facility name"] == "Station – west"
    (factor,) = calculate_factors(loaded)
    assert factor.direct_gco2e_per_kwh == 40


def test_published_results_are_reproducible(tmp_path):
    factors = calculate_factors(read_nger(DATA_DIR / "nger_2024_25.csv"))
    path = tmp_path / "results.csv"
    write_factors(factors, path)
    assert path.read_bytes() == (DATA_DIR / "results.csv").read_bytes()
    assert len(factors) == 14


def test_output_sorting_and_rounding_happen_after_aggregation(tmp_path):
    (factor,) = calculate_factors([facility(**{GENERATION_COLUMN: "300"})])
    path = tmp_path / "output.csv"
    write_factors([replace(factor, zone="AU-NSW")], path)
    (row,) = list(csv.DictReader(path.open()))
    assert row["direct_gco2e_per_kwh"] == "133.33"
