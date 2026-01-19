"""
This library contains validation functions applied to all parsers by the feeder.
This is a higher level validation than validation.py
"""

from datetime import datetime, timezone
from typing import Any

from electricitymap.contrib.config import EXCHANGES_CONFIG
from electricitymap.contrib.types import ZoneKey


class ValidationError(ValueError):
    pass


def validate_datapoint_format(datapoint: dict[str, Any], kind: str, zone_key: ZoneKey):
    """
    Checks that a datapoint has the required keys. A parser can only be merged if the datapoints for each function have the correct format.
    """
    standard_keys = ["datetime", "source"]
    keys_dict = {
        "consumption": ["zoneKey", "consumption"] + standard_keys,
        "exchange": ["sortedZoneKeys", "netFlow"] + standard_keys,
        "price": ["zoneKey", "currency", "price"] + standard_keys,
        "consumptionForecast": ["zoneKey", "value"] + standard_keys,
        "productionPerModeForecast": ["zoneKey", "production"] + standard_keys,
        "generationForecast": ["zoneKey", "value"] + standard_keys,
        "exchangeForecast": ["zoneKey", "netFlow"] + standard_keys,
    }
    for key in keys_dict[kind]:
        if key not in datapoint:
            raise ValidationError(
                f"{zone_key} - data point does not have the required keys:  {[key for key in keys_dict[kind] if key not in datapoint]} is missing"
            )


def validate_reasonable_time(item, k):
    data_dt = item["datetime"].astimezone(timezone.utc)
    now = datetime.now(timezone.utc)

    if data_dt.year < 2000:
        raise ValidationError(
            f"Data from {k} can't be before year 2000, it was from: {data_dt}"
        )
    if data_dt > now:
        raise ValidationError(
            f"Data from {k} can't be in the future, it was from {data_dt}, now is {now}"
        )


def validate_consumption(obj: dict, zone_key: ZoneKey) -> None:
    validate_datapoint_format(datapoint=obj, kind="consumption", zone_key=zone_key)
    if (obj.get("consumption") or 0) < 0:
        raise ValidationError(
            f"{zone_key}: consumption has negative value {obj['consumption']}"
        )
    # Plausibility Check, no more than 500GW
    if abs(obj.get("consumption") or 0) > 500000:
        raise ValidationError(
            f"{zone_key}: consumption is not realistic (>500GW) {obj['consumption']}"
        )
    validate_reasonable_time(obj, zone_key)


def validate_exchange(item, k) -> None:
    validate_datapoint_format(datapoint=item, kind="exchange", zone_key=k)
    if item.get("sortedZoneKeys", None) != k:
        raise ValidationError(
            f"Sorted country codes {item.get('sortedZoneKeys', None)} and {k} don't match"
        )
    if "datetime" not in item:
        raise ValidationError(f"datetime was not returned for {k}")
    if not isinstance(item["datetime"], datetime):
        raise ValidationError(f"datetime {item['datetime']} is not valid for {k}")
    validate_reasonable_time(item, k)
    if "netFlow" not in item:
        raise ValidationError(f"netFlow was not returned for {k}")
    # Verify that the exchange flow is not greater than the interconnector
    # capacity and has physical sense (no exchange should exceed 100GW)
    # Use https://github.com/electricitymaps/electricitymaps-contrib/blob/master/parsers/examples/example_parser.py for expected format
    if item.get("sortedZoneKeys", None) and item.get("netFlow", None):
        zone_names: list[str] = item["sortedZoneKeys"]
        if abs(item.get("netFlow", 0)) > 100000:
            raise ValidationError(
                f"netFlow {item['netFlow']} exceeds physical plausibility (>100GW) for {k}"
            )
        if (
            len(zone_names) == 2
            and (zone_names in EXCHANGES_CONFIG)
            and ("capacity" in EXCHANGES_CONFIG[zone_names])
        ):
            interconnector_capacities = EXCHANGES_CONFIG[zone_names]["capacity"]
            margin = 0.1
            if not (
                min(interconnector_capacities) * (1 - margin)
                <= item["netFlow"]
                <= max(interconnector_capacities) * (1 + margin)
            ):
                raise ValidationError(
                    f"netFlow {item['netFlow']} exceeds interconnector capacity for {k}"
                )
