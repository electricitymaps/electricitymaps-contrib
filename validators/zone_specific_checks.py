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
