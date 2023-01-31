import pandas as pd

from validators.lib.config import validator


@validator(
    kind="production",
    not_zone_keys=[  # zone_keys where we allow fossil fuel production to be 0
        "CH",
        "NO",
        "AU-TAS",
        "DK-BHM",
        "US-CAR-YAD",
        "US-NW-SCL",
        "US-NW-CHPD",
        "US-NW-WWA",
        "US-NW-GCPD",
        "US-NW-TPWR",
        "US-NW-WAUW",
        "US-SE-SEPA",
        "US-NW-GWA",
        "US-NW-DOPD",
        "US-NW-AVRN",
        "LU",
    ],
)
def validate_production_has_fossil_fuel(events: pd.DataFrame) -> pd.Series:
    """
    Validate that the production has fossil fuel.
    """
    fossil_fuel_cols = [
        "production.unknown",
        "production.coal",
        "production.oil",
        "production.gas",
    ]
    fossil_fuel_cols_in_event = set.intersection(
        set(fossil_fuel_cols), set(events.columns)
    )

    res = (events[fossil_fuel_cols_in_event] > 0).any(axis=1).astype(int)
    return res


@validator(
    kind="production",
    zone_keys=[  # zone_keys where we allow fossil fuel production to be 0
        "US-CAR-YAD",
    ],
)
def validate_hydro_production_is_possible(events: pd.DataFrame) -> pd.Series:
    """
    In US-CAR-YAD, there is only hydro production coming from 4 dams.
    As seen here https://openinframap.org/#10.29/35.4745/-80.1301,
    the total capacity is around 215 MW of run of the river hydro.
    Sometimes the EIA reports production of less than 5 MW which is unrealistic.
    """
    MIN_HYDRO_PRODUCTION = 5
    res = (events["production.hydro"] > MIN_HYDRO_PRODUCTION).astype(int)
    return res
