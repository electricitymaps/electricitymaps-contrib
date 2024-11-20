import pandas as pd
import pytest
from numpy import nan

from electricitymap.contrib.parsers.DO import correct_solar_production


@pytest.fixture
def production_df():
    d = {
        "wind": {
            pd.Timestamp("2024-04-18 00:00:00-0400", tz="America/Dominica"): 117.42,
            pd.Timestamp("2024-04-18 01:00:00-0400", tz="America/Dominica"): 76.37,
            pd.Timestamp("2024-04-18 02:00:00-0400", tz="America/Dominica"): 53.67,
            pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica"): 57.76,
            pd.Timestamp("2024-04-18 04:00:00-0400", tz="America/Dominica"): 64.95,
            pd.Timestamp("2024-04-18 05:00:00-0400", tz="America/Dominica"): 52.9,
            pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica"): 46.25,
            pd.Timestamp("2024-04-18 07:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 08:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 09:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 10:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 11:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 12:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 13:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 14:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 15:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 16:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 17:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 18:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 19:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 20:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 21:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 22:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 23:00:00-0400", tz="America/Dominica"): nan,
        },
        "solar": {
            pd.Timestamp("2024-04-18 00:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 01:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 02:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 04:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 05:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 07:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 08:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 09:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 10:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 11:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 12:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 13:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 14:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 15:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 16:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 17:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 18:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 19:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 20:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 21:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 22:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 23:00:00-0400", tz="America/Dominica"): nan,
        },
        "hydro": {
            pd.Timestamp("2024-04-18 00:00:00-0400", tz="America/Dominica"): 144.47,
            pd.Timestamp("2024-04-18 01:00:00-0400", tz="America/Dominica"): 75.34,
            pd.Timestamp("2024-04-18 02:00:00-0400", tz="America/Dominica"): 72.94,
            pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica"): 84.23,
            pd.Timestamp("2024-04-18 04:00:00-0400", tz="America/Dominica"): 84.52,
            pd.Timestamp("2024-04-18 05:00:00-0400", tz="America/Dominica"): 84.68,
            pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica"): 87.36,
            pd.Timestamp("2024-04-18 07:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 08:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 09:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 10:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 11:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 12:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 13:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 14:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 15:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 16:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 17:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 18:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 19:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 20:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 21:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 22:00:00-0400", tz="America/Dominica"): nan,
            pd.Timestamp("2024-04-18 23:00:00-0400", tz="America/Dominica"): nan,
        },
    }
    return pd.DataFrame(d)


def test_correct_solar_production_all_nan(production_df):
    corrected_df = correct_solar_production(production_df)
    assert corrected_df["solar"].isna().all()


def test_correct_solar_production_nan_then_prod(production_df):
    production_df["solar"].loc[
        pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica")
    ] = 12
    corrected_df = correct_solar_production(production_df)
    assert (
        corrected_df["solar"].loc[
            pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica")
        ]
        == 12
    )
    assert all(
        corrected_df["solar"].loc[
            : pd.Timestamp("2024-04-18 05:00:00-0400", tz="America/Dominica")
        ]
        == 0
    )
    assert all(
        corrected_df["solar"]
        .loc[pd.Timestamp("2024-04-18 07:00:00-0400", tz="America/Dominica") :]
        .isnull()
    )


def test_correct_solar_production_prod_then_nan(production_df):
    production_df["solar"].loc[
        : pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica")
    ] = 12
    corrected_df = correct_solar_production(production_df)
    assert all(
        corrected_df["solar"].loc[
            : pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica")
        ]
        == 12
    )


def test_correct_solar_production_prod_then_nan_then_prod(production_df):
    production_df["solar"].loc[
        : pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica")
    ] = 12
    production_df["solar"].loc[
        pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica")
    ] = 14
    corrected_df = correct_solar_production(production_df)
    assert all(
        corrected_df["solar"].loc[
            : pd.Timestamp("2024-04-18 03:00:00-0400", tz="America/Dominica")
        ]
        == 12
    )
    assert (
        corrected_df["solar"].loc[
            pd.Timestamp("2024-04-18 06:00:00-0400", tz="America/Dominica")
        ]
        == 14
    )
    assert all(
        corrected_df["solar"].loc[
            pd.Timestamp(
                "2024-04-18 04:00:00-0400", tz="America/Dominica"
            ) : pd.Timestamp("2024-04-18 05:00:00-0400", tz="America/Dominica")
        ]
        == 0
    )
    assert all(
        corrected_df["solar"]
        .loc[pd.Timestamp("2024-04-18 07:00:00-0400", tz="America/Dominica") :]
        .isnull()
    )
