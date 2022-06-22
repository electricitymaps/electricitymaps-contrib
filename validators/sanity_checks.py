from datetime import datetime

import numpy as np
import pandas as pd

from electricitymap.contrib.config import EXCHANGES_CONFIG
from electricitymap.contrib.validators.lib.config import validator


@validator(kind="production")
def validate_positive_production(events: pd.DataFrame) -> pd.Series:
    """
    Validate that the production is positive. (Allows nan values)
    """
    production_cols = [col for col in events if col.startswith("production")]
    res = 1 - (events[production_cols] < 0).any(axis=1).astype(int)
    return res


@validator(kind="production")
def validate_production_one_non_nan_value(events: pd.DataFrame) -> pd.Series:
    """
    Validate that the production has at least one non-nan value.
    """
    production_cols = [col for col in events if col.startswith("production")]
    res = events[production_cols].notnull().any(axis=1).astype(int)
    return res


@validator(kind="production")
def validate_production_is_plausible(events: pd.DataFrame) -> pd.Series:
    """
    Validates that the production doesn't exceed 500GW
    """
    production_cols = [col for col in events if col.startswith("production")]
    res = (events.fillna(0)[production_cols] < 500000).all(axis=1).astype(int)
    return res


@validator(kind="production")
def validate_reasonable_time_production(events: pd.DataFrame) -> pd.Series:
    """
    Validates that the datetime is > year 2000 and not in the future
    """
    evaluation = (events.index > "2000-01-01") & (
        events.index < datetime.now().isoformat()
    )
    res = pd.Series(evaluation, index=events.index).astype(int)
    return res


@validator(kind="exchange")
def validate_reasonable_time_exchange(events: pd.DataFrame) -> pd.Series:
    """
    (Same test as `validate_reasonable_time_production`, but for exchange)
    Validates that the datetime is > year 2000 and not in the future
    """
    evaluation = (events.index > "2000-01-01") & (
        events.index < datetime.now().isoformat()
    )
    res = pd.Series(evaluation, index=events.index).astype(int)
    return res


@validator(kind="exchange")
def validate_exchange_netflow_is_plausible(events: pd.DataFrame) -> pd.Series:
    """
    Validates that exchanges doesn't exceed 100GW
    """
    res = (abs(events["netFlow"]) < 100000).astype(int)
    return res


@validator(kind="exchange")
def validate_exchange_netflow_doesnt_exceed_capacity(
    events: pd.DataFrame, zone_key: str
) -> pd.Series:
    """
    Validates that exchanges doesn't exceed the interconnector capacity by more than 10%
    """
    ALLOWED_MARGIN = 1.1
    interconnector_capacities = EXCHANGES_CONFIG[zone_key].get("capacity", [-np.inf, np.inf])

    res = (
        (min(interconnector_capacities) * ALLOWED_MARGIN <= events["netFlow"])
        & (events["netFlow"] <= max(interconnector_capacities) * ALLOWED_MARGIN)
    ).astype(int)

    return res
