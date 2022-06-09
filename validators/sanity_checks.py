import pandas as pd

from validators.lib.config import validator


@validator(kind="production")
def validate_positive_production(events: pd.DataFrame) -> pd.Series:
    """
    Validate that the production is positive. (Allows nan values)
    """
    production_cols = [col for col in events if col.startswith("production")]
    res = (events[production_cols] < 0).any(axis=1).astype(int)
    return res


@validator(kind="production")
def validate_production_one_non_nan_value(events: pd.DataFrame) -> pd.Series:
    """
    Validate that the production has at least one non-nan value.
    """
    production_cols = [col for col in events if col.startswith("production")]
    res = 1 - events[production_cols].notnull().any(axis=1).astype(int)
    return res
