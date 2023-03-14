"""Centralised validation function for all parsers."""

import math
from logging import Logger, getLogger
from typing import Any, Dict, List, Tuple, Union

import numpy as np
import pandas as pd


def has_value_for_key(datapoint: Dict[str, Any], key: str, logger: Logger):
    """
    Checks that the key exists in datapoint and that the corresponding value is not None.
    """
    value = datapoint["production"].get(key, None)
    if value is None or math.isnan(value):
        logger.warning(
            "Required generation type {} is missing from {}".format(
                key, datapoint["zoneKey"]
            ),
            extra={"key": datapoint["zoneKey"]},
        )
        return None
    return True


def check_expected_range(
    datapoint: Dict[str, Any],
    value: Union[float, int],
    expected_range: Tuple[float, float],
    logger: Logger,
    key: Union[str, None] = None,
):
    low, high = min(expected_range), max(expected_range)
    if not (low <= value <= high):
        key_str = "for key `{}`".format(key) if key else ""
        logger.warning(
            "{} reported total of {:.2f}MW falls outside range "
            "of {} {}".format(datapoint["zoneKey"], value, expected_range, key_str),
            extra={"key": datapoint["zoneKey"]},
        )
        return
    return True


def validate_production_diffs(
    datapoints: List[Dict[str, Any]], max_diff: Dict, logger: Logger
):
    """
    Parameters
    ----------
    datapoints: a list of datapoints having a 'production' field
    max_diff: dict representing the max allowed diff (in MW) per energy type
    logger

    Returns
    -------
    the same list of datapoints, with the ones having a too big diff removed
    """

    if len(datapoints) < 2:
        return datapoints

    # ignore points that are None
    # TODO(olc): do diffs on each chunks of consecutive non-None points
    # intead of simply remove None
    datapoints = [x for x in datapoints if x]

    # sort datapoins by datetime
    datapoints = sorted(datapoints, key=lambda x: x["datetime"])

    ok_diff = pd.Series(np.ones_like(datapoints, dtype=bool))
    for energy, max_diff in max_diff.items():
        if "energy" == "total":
            series = pd.Series(
                [
                    np.nansum([v for v in datapoint["production"].values()])
                    for datapoint in datapoints
                ]
            )
        else:
            series = pd.Series(
                [
                    datapoint["production"].get(energy, np.nan)
                    for datapoint in datapoints
                ]
            )
        # nan is always allowed (can be disallowed using `validate` function)
        new_diffs = (np.abs(series.diff()) < max_diff) | series.isna()
        if not new_diffs[1:].all():
            wrongs_ixs = new_diffs[~new_diffs].index
            wrongs_ixs_and_previous = sorted(
                {ix - 1 for ix in wrongs_ixs} | set(wrongs_ixs)
            )
            to_display = [
                (datapoints[i]["datetime"], datapoints[i]["production"][energy])
                for i in wrongs_ixs_and_previous
                if i > 0
            ]
            logger.warning(
                "some datapoints have a too high production value difference "
                "for {}: {}".format(energy, to_display)
            )
        ok_diff &= new_diffs
    # first datapoint is always OK
    ok_diff.iloc[0] = True

    return [datapoints[i] for i in ok_diff[ok_diff].index]


def validate_consumption(
    datapoint: Dict, logger: Union[Logger, None]
) -> Union[Dict[str, Any], None]:
    """
    Validates a production datapoint based on given constraints.
    If the datapoint is found to be invalid then None is returned.
    """
    if logger is None:
        logger = getLogger(__name__)
    consumption: float = datapoint["consumption"]
    if consumption == 0:
        logger.warning(
            "{} reported total of {}MW, expected consumption cannot be null".format(
                datapoint["zoneKey"], consumption
            ),
            extra={"key": datapoint["zoneKey"]},
        )
        return
    return datapoint


def validate_exchange(
    datapoint: Dict, logger: Logger = getLogger(__name__)
) -> Union[Dict[str, Any], None]:
    """
    Validates a production datapoint based on given constraints.
    If the datapoint is found to be invalid then None is returned.
    """
    exchange: float = datapoint["netFlow"]
    if exchange is None:
        logger.warning(
            "{}: expected exchange cannot be null".format(
                datapoint["sortedZoneKeys"], exchange
            ),
            extra={"key": datapoint["sortedZoneKeys"]},
        )
        return
    return datapoint


def validate(
    datapoint: Dict, logger: Union[Logger, None], **kwargs
) -> Union[Dict[str, Any], None]:
    """
    Validates a production datapoint based on given constraints.
    If the datapoint is found to be invalid then None is returned.

    Arguments
    ---------
    logger
    datapoint: a production datapoint. See examples
    optional keyword arguments
        remove_negative: bool
            Changes negative production values to None.
            Defaults to False.
        required: list
            Generation types that must be present.
            For example ['gas', 'hydro']
            If any of these types are None the datapoint will be invalidated.
            Defaults to an empty list.
        floor: float | int
            Checks production sum is above floor value.
            If this is not the case the datapoint is invalidated.
            Defaults to None
        expected_range: tuple | dict
            Checks production total against expected range.
            Tuple is in form (low threshold, high threshold), e.g. (1800, 12000).
            If a dict, it should be in the form
            {
            'nuclear': (low, high),
            'coal': (low, high),
            }
        fake_zeros: bool
            Check if there are fake zeros, eg all values are 0 or None
        All keys will be required.
        If the total is outside this range the datapoint will be invalidated.
        Defaults to None.

    Examples
    --------
    >>> test_datapoint = {
    >>>   'zoneKey': 'FR',
    >>>   'datetime': '2017-01-01T00:00:00Z',
    >>>       'production': {
    >>>           'biomass': 50.0,
    >>>           'coal': 478.0,
    >>>           'gas': 902.7,
    >>>           'hydro': 190.1,
    >>>           'nuclear': None,
    >>>           'oil': 0.0,
    >>>           'solar': 20.0,
    >>>           'wind': 40.0,
    >>>           'geothermal': 0.0,
    >>>           'unknown': 6.0
    >>>       },
    >>>       'storage': {
    >>>           'hydro': -10.0,
    >>>       },
    >>>       'source': 'mysource.com'
    >>> }
    >>> validate(datapoint, None, required=['gas'], expected_range=(100, 2000))
    datapoint
    >>> validate(datapoint, None, required=['not_a_production_type'])
    None
    >>> validate(datapoint, None, required=['gas'],
    >>>          expected_range={'solar': (0, 1000), 'wind': (100, 2000)})
    datapoint
    """
    if logger is None:
        logger = getLogger(__name__)

    remove_negative: bool = kwargs.pop("remove_negative", False)
    required: list[Any] = kwargs.pop("required", [])
    floor: Union[float, int, None] = kwargs.pop("floor", None)
    expected_range: Union[Tuple, Dict, None] = kwargs.pop("expected_range", None)
    fake_zeros: bool = kwargs.pop("fake_zeros", False)

    if kwargs:
        raise TypeError("Unexpected **kwargs: %r" % kwargs)

    generation: Dict[str, Any] = datapoint["production"]
    storage: Dict[str, Any] = datapoint.get("storage", {})

    if remove_negative:
        for key, val in generation.items():
            if val is not None and -5.0 < val < 0.0:
                logger.warning(
                    "{} returned {:.2f}, setting to None".format(key, val),
                    extra={"key": datapoint["zoneKey"]},
                )
                generation[key] = None

    if required:
        for item in required:
            if not has_value_for_key(datapoint, item, logger):
                return

    if floor:
        # when adding power to the system, storage key is negative
        total = sum(v for k, v in generation.items() if v is not None) - sum(
            v for k, v in storage.items() if v is not None
        )
        if total < floor:
            logger.warning(
                "{} reported total of {}MW does not meet {}MW floor"
                " value".format(datapoint["zoneKey"], total, floor),
                extra={"key": datapoint["zoneKey"]},
            )
            return

    if expected_range:
        if isinstance(expected_range, dict):
            for key, range_ in expected_range.items():
                if not has_value_for_key(datapoint, key, logger):
                    return
                if not check_expected_range(
                    datapoint, generation[key], range_, logger, key=key
                ):
                    return
        else:
            # when adding power to the system, storage key is negative
            total = sum(v for k, v in generation.items() if v is not None) - sum(
                v for k, v in storage.items() if v is not None
            )
            if not check_expected_range(datapoint, total, expected_range, logger):
                return

    if fake_zeros:
        if all((val == 0) or (val is None) for val in generation.values()):
            logger.warning(
                f"{datapoint['zoneKey']} - {datapoint['datetime']}: unrealistic datapoint, all production values are 0.0 MW or null"
            )
            return

    return datapoint


test_datapoint = {
    "zoneKey": "FR",
    "datetime": "2017-01-01T00:00:00Z",
    "production": {
        "biomass": 50.0,
        "coal": 478.0,
        "gas": 902.7,
        "hydro": 190.1,
        "nuclear": None,
        "oil": 0.0,
        "solar": 20.0,
        "wind": 40.0,
        "geothermal": -1.0,
        "unknown": 6.0,
    },
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}


test_datapoint_consumption = {
    "zoneKey": "IN-NO",
    "datetime": "2017-01-01T00:00:00Z",
    "consumption": 0,
    "source": "mysource.com",
}


if __name__ == "__main__":
    print(validate_consumption(test_datapoint_consumption, None))
