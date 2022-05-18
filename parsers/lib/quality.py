"""
This library contains validation functions applied to all parsers by the feeder.
This is a higher level validation than validation.py
"""
import datetime
import warnings

import arrow

from electricitymap.contrib.config import EXCHANGES_CONFIG, emission_factors


class ValidationError(ValueError):
    pass


def validate_reasonable_time(item, k):
    data_time = arrow.get(item["datetime"])
    if data_time.year < 2000:
        raise ValidationError(
            "Data from %s can't be before year 2000, it was " "%s" % (k, data_time)
        )

    arrow_now = arrow.utcnow()
    if data_time > arrow_now:
        raise ValidationError(
            "Data from %s can't be in the future, data was %s, now is "
            "%s" % (k, data_time, arrow_now)
        )


def validate_consumption(obj, zone_key):
    if (obj.get("consumption") or 0) < 0:
        raise ValidationError(
            "%s: consumption has negative value " "%s" % (zone_key, obj["consumption"])
        )
    # Plausibility Check, no more than 500GW
    if abs(obj.get("consumption") or 0) > 500000:
        raise ValidationError(
            "%s: consumption is not realistic (>500GW) "
            "%s" % (zone_key, obj["consumption"])
        )
    validate_reasonable_time(obj, zone_key)


def validate_exchange(item, k):
    if item.get("sortedZoneKeys", None) != k:
        raise ValidationError(
            "Sorted country codes %s and %s don't "
            "match" % (item.get("sortedZoneKeys", None), k)
        )
    if "datetime" not in item:
        raise ValidationError("datetime was not returned for %s" % k)
    if type(item["datetime"]) != datetime.datetime:
        raise ValidationError("datetime %s is not valid for %s" % (item["datetime"], k))
    validate_reasonable_time(item, k)
    # Verify that the exchange flow is not greater than the interconnector
    # capacity and has physical sense (no exchange should exceed 100GW)
    # Use https://github.com/tmrowco/electricitymap-contrib/blob/master/parsers/example.py for expected format
    if item.get("sortedZoneKeys", None) and item.get("netFlow", None):
        zone_names = item["sortedZoneKeys"]
        if abs(item.get("netFlow", 0)) > 100000:
            raise ValidationError(
                "netFlow %s exceeds physical plausibility (>100GW) for %s"
                % (item["netFlow"], k)
            )
        if len(zone_names) == 2:
            if (zone_names in EXCHANGES_CONFIG) and (
                "capacity" in EXCHANGES_CONFIG[zone_names]
            ):
                interconnector_capacities = EXCHANGES_CONFIG[zone_names]["capacity"]
                margin = 0.1
                if not (
                    min(interconnector_capacities) * (1 - margin)
                    <= item["netFlow"]
                    <= max(interconnector_capacities) * (1 + margin)
                ):
                    raise ValidationError(
                        "netFlow %s exceeds interconnector capacity for %s"
                        % (item["netFlow"], k)
                    )


def validate_production(obj, zone_key):
    if "datetime" not in obj:
        raise ValidationError("datetime was not returned for %s" % zone_key)
    if "countryCode" in obj:
        warnings.warn(
            "object has field `countryCode`. It should have "
            "`zoneKey` instead. In {}".format(obj)
        )
    if "zoneKey" not in obj and "countryCode" not in obj:
        raise ValidationError("zoneKey was not returned for %s" % zone_key)
    if not isinstance(obj["datetime"], datetime.datetime):
        raise ValidationError(
            "datetime %s is not valid for %s" % (obj["datetime"], zone_key)
        )
    if (obj.get("zoneKey", None) or obj.get("countryCode", None)) != zone_key:
        raise ValidationError(
            "Zone keys %s and %s don't match in %s"
            % (obj.get("zoneKey", None), zone_key, obj)
        )

    if (
        obj.get("production", {}).get("unknown", None) is None
        and obj.get("production", {}).get("coal", None) is None
        and obj.get("production", {}).get("oil", None) is None
        and obj.get("production", {}).get("gas", None) is None
        and zone_key
        not in [
            "CH",
            "NO",
            "AUS-TAS",
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
        ]
    ):
        raise ValidationError(
            "Coal, gas or oil or unknown production value is required for"
            " %s" % zone_key
        )
    if obj.get("storage"):
        if not isinstance(obj["storage"], dict):
            raise ValidationError(
                "storage value must be a dict, was " "{}".format(obj["storage"])
            )
        not_allowed_keys = set(obj["storage"]) - {"battery", "hydro"}
        if not_allowed_keys:
            raise ValidationError(
                "unexpected keys in storage: {}".format(not_allowed_keys)
            )
    for key, value in obj["production"].items():
        if value is None:
            continue
        if value < 0:
            raise ValidationError(
                "%s: key %s has negative value %s" % (zone_key, key, value)
            )
        # Plausibility Check, no more than 500GW
        if value > 500000:
            raise ValidationError(
                "%s: production for %s is not realistic ("
                ">500GW) "
                "%s" % (zone_key, key, value)
            )

    for key in obj.get("production", {}).keys():
        if key not in emission_factors(zone_key).keys():
            raise ValidationError(
                "Couldn't find emission factor for '%s' in '%s'. Maybe you misspelled one of the production keys?"
                % (key, zone_key)
            )

    validate_reasonable_time(obj, zone_key)
