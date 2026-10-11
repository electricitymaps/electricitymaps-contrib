from datetime import datetime
from json import dumps
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from pandas.testing import assert_series_equal

from electricitymap.contrib.parsers import IN
from electricitymap.contrib.parsers.IN import (
    compute_zone_key_share_per_mode_out_of_total,
    parse_15m_production_grid_india_report,
    parse_daily_production_grid_india_report,
    parse_daily_total_production_grid_india_report,
    parse_total_production_15min_grid_india_report,
    scale_15min_production,
)
from electricitymap.contrib.parsers.lib.exceptions import ParserException

file_path = Path(__file__).parent / "mocks" / "IN" / "08.04.25_NLDC_PSP.xls"
content = file_path.read_bytes()


def test_parse_daily_total_production_grid_india_report():
    result = parse_daily_total_production_grid_india_report(content)
    assert result == 5404120.0


def test_parse_total_production_15min_grid_india_report():
    result = parse_total_production_15min_grid_india_report(content)
    assert result == 5035435.25


def test_compute_zone_key_share_per_mode_out_of_total():
    result = compute_zone_key_share_per_mode_out_of_total(content, "IN-NO")
    expected = pd.Series(
        data={
            "nuclear": 0.1870051375037776,
            "wind": 0.24537248628884828,
            "solar": 0.4077671888420794,
            "hydro": 0.5168968557155451,
            "gas": 0.18445718445718445,
            "coal": 0.21282309665243412,
            "unknown": 0.2750799208403111,
        },
        name="value",
    )
    expected.index.name = "mode"
    assert_series_equal(result.sort_index(), expected.sort_index())


def test_scale_15min_production(snapshot):
    generation_scaling_factor = 0.5
    result = scale_15min_production(content, generation_scaling_factor)
    result_dict = result.to_dict(orient="records")
    snapshot.assert_match(dumps(result_dict, indent=2))


def test_parse_15m_production_grid_india_report(snapshot):
    result = parse_15m_production_grid_india_report(
        content, "IN-NO", datetime(2025, 4, 8, 0, 0)
    )
    assert snapshot == result


def test_parse_daily_production_grid_india_report(snapshot):
    # This test uses the same file as the one for the 15m production report, but it does not use the 15m data.
    # This is to test the behavior of the parser for the period 2023/04/01 - 2024/11/04.
    result = parse_daily_production_grid_india_report(
        content, "IN-EA", datetime(2025, 4, 8, 0, 0)
    )
    assert snapshot == result


def test_parse_production_from_cea_npp_without_conventional_production_returns_no_data():
    with (
        patch.object(IN, "fetch_cea_production", return_value={}),
        patch.object(
            IN, "fetch_npp_production", side_effect=ParserException("IN.py", "no data")
        ),
    ):
        assert (
            IN.parse_production_from_cea_npp(
                zone_key="IN-NO", target_datetime=datetime(2024, 1, 1)
            )
            == []
        )
