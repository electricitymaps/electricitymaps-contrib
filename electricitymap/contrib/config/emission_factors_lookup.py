from datetime import datetime, timezone
from operator import itemgetter
from typing import Any

from electricitymap.contrib.config import (
    CO2EQ_PARAMETERS_DIRECT,
    CO2EQ_PARAMETERS_LIFECYCLE,
    ZONE_PARENT,
    ZONES_CONFIG,
)
from electricitymap.contrib.config.constants import ENERGIES
from electricitymap.contrib.config.model import (
    EmissionFactorVariant,
    YearZoneModeEmissionFactor,
)
from electricitymap.contrib.lib.types import ZoneKey


def get_zone_specific_co2eq_parameter(
    co2eq_parameters: dict,
    zone_key: str,
    key: str,
    sub_key: str,
    dt: datetime,
    metadata: bool = False,
) -> dict[str, float]:
    if metadata:
        return _get_zone_specific_co2eq_parameter_with_metadata(
            co2eq_parameters=co2eq_parameters,
            zone_key=zone_key,
            key=key,
            sub_key=sub_key,
            dt=dt,
        )
    else:
        return _get_zone_specific_co2eq_parameter_no_metadata(
            co2eq_parameters=co2eq_parameters,
            zone_key=zone_key,
            key=key,
            sub_key=sub_key,
            dt=dt,
        )


def _get_zone_specific_co2eq_parameter_no_metadata(
    co2eq_parameters: dict, zone_key: str, key: str, sub_key: str, dt: datetime
) -> dict[str, float]:  # TODO: actually this returns Union[Dict, bool]
    """Accessor for co2eq_parameters.
    If Available, it will return the zoneOverride value. If not, it will return the default value.

    Args:
        co2eq_parameters (dict): The dictionary to read from.
        zone_key (str): The zone_key to try and find a zoneOverride for.
        key (str): The key of the parameter to find.
        sub_key (str): The specific sub key inside the parameter that you want to access
        dt (datetime): Will return the most recent co2eq for that dt. For the latest co2eq, pass `datetime.max`

    Raises:
        ValueError: Raised when both the zoneOverride and default value is unavailable
    """
    # TODO this doesn't raise a ValueError at the moment. Which gives typing errors because it can return None.
    params = co2eq_parameters[key]
    zone_key = ZoneKey(zone_key)

    defaults = params["defaults"][sub_key]
    zone_override = params["zoneOverrides"].get(zone_key, {}).get(sub_key, None)
    # If no entry was found, use the parent if it exists
    if ZONE_PARENT.get(zone_key) and not zone_override:
        zone_override = (
            params["zoneOverrides"].get(ZONE_PARENT[zone_key], {}).get(sub_key, None)
        )

    res = None
    res = zone_override if zone_override is not None else defaults

    if isinstance(res, list):
        # `n` dates are sorted in ascending order (d1, d2, ..., dn)
        # d1 is valid from from (epoch to d2)
        # d2 is valid from (d2 to d3)
        # dn is valid from (dn to end_of_time)

        if len(res) == 0:
            raise ValueError(
                f"Error in given co2eq_parameters. List is empty for [{zone_key}, {key}, {sub_key}]"
            )

        res.sort(key=itemgetter("datetime"))
        dt = dt.replace(tzinfo=timezone.utc)
        for co2eq in reversed(res):
            co2eq_dt = datetime.fromisoformat(co2eq["datetime"]).replace(
                tzinfo=timezone.utc
            )
            if co2eq_dt <= dt:
                return co2eq  # type: ignore[no-any-return]
        breakpoint()
        return res[0]  # type: ignore[no-any-return]

    else:
        return res  # type: ignore[no-any-return]


def _get_zone_specific_co2eq_parameter_with_metadata(
    co2eq_parameters: dict,
    zone_key: str,
    key: str,
    sub_key: str,
    dt: datetime,
) -> dict[str, Any]:
    """
    Lookup logic identical to get_zone_specific_co2eq_parameter.
    Adds a 'variant' field that provides context about where an emission factor comes from.
    Variant selection logic:

    GLOBAL/ZONE -> defined in config/defaults.yaml or config/zones/<zone_key>.yaml

    *_EXACT_TIMELESS -> no "datetime"
    *_EXACT_TIMELY -> has "datetime" and "datetime".year == dt.year
    *_FALLBACK_LATEST -> has "datetime" and max("datetime").year < dt.year
    *_FALLBACK_OLDER -> has "datetime" and max("datetime").year < dt.year < min("datetime").year and is not EXACT
    *_FALLBACK_OLDEST -> has "datetime" and dt.year < min("datetime").year
    """
    params = co2eq_parameters[key]
    zone_key = ZoneKey(zone_key)

    defaults = params["defaults"][sub_key]
    zone_override = params["zoneOverrides"].get(zone_key, {}).get(sub_key, None)
    # If no entry was found, use the parent if it exists
    if ZONE_PARENT.get(zone_key) and not zone_override:
        zone_override = (
            params["zoneOverrides"].get(ZONE_PARENT[zone_key], {}).get(sub_key, None)
        )

    res = None
    res = zone_override if zone_override is not None else defaults

    if isinstance(res, list):
        # `n` dates are sorted in ascending order (d1, d2, ..., dn)
        # d1 is valid from from (epoch to d2)
        # d2 is valid from (d2 to d3)
        # dn is valid from (dn to end_of_time)

        if len(res) == 0:
            raise ValueError(
                f"Error in given co2eq_parameters. List is empty for [{zone_key}, {key}, {sub_key}]"
            )

        res.sort(key=itemgetter("datetime"))
        dt = dt.replace(tzinfo=timezone.utc)
        for i, co2eq in enumerate(reversed(res)):
            co2eq_dt = datetime.fromisoformat(co2eq["datetime"]).replace(
                tzinfo=timezone.utc
            )
            if co2eq_dt <= dt:
                ret = co2eq

                ef_year = co2eq_dt.year
                dt_year = dt.year
                if ef_year == dt_year:
                    if zone_override:
                        variant = EmissionFactorVariant.ZONE_EXACT_TIMELY
                    else:
                        variant = EmissionFactorVariant.GLOBAL_EXACT_TIMELY
                elif ef_year < dt_year:
                    if i == 0:
                        if zone_override:
                            variant = EmissionFactorVariant.ZONE_FALLBACK_LATEST
                        else:
                            variant = EmissionFactorVariant.GLOBAL_FALLBACK_LATEST
                    else:
                        if zone_override:
                            variant = EmissionFactorVariant.ZONE_FALLBACK_OLDER
                        else:
                            variant = EmissionFactorVariant.GLOBAL_FALLBACK_OLDER

                ret["variant"] = variant.value
                return ret

        # res is sorted in ascending order, if we get here
        # it means dt < res[0]["datetime"]
        ret = res[0]
        if zone_override:
            variant = EmissionFactorVariant.ZONE_FALLBACK_OLDEST
        else:
            variant = EmissionFactorVariant.GLOBAL_FALLBACK_OLDEST
        ret["variant"] = variant.value
        return ret

    else:
        # res is not a list, which implies it's a dict
        # there are two kinds of dicts
        # if it has "datetime" then it's timely
        # else it's timeless
        ret = res
        ret_dt = res.get("datetime")
        if ret_dt is None:
            if zone_override:
                variant = EmissionFactorVariant.ZONE_EXACT_TIMELESS
            else:
                variant = EmissionFactorVariant.GLOBAL_EXACT_TIMELESS
        else:
            ret_dt_year = (
                datetime.fromisoformat(ret_dt).replace(tzinfo=timezone.utc).year
            )
            dt_year = dt.year
            if ret_dt_year == dt_year:
                if zone_override:
                    variant = EmissionFactorVariant.ZONE_EXACT_TIMELY
                else:
                    variant = EmissionFactorVariant.GLOBAL_EXACT_TIMELY
            elif ret_dt_year < dt_year:
                if zone_override:
                    variant = EmissionFactorVariant.ZONE_FALLBACK_LATEST
                else:
                    variant = EmissionFactorVariant.GLOBAL_FALLBACK_LATEST
            else:
                if zone_override:
                    variant = EmissionFactorVariant.ZONE_FALLBACK_OLDEST
                else:
                    variant = EmissionFactorVariant.GLOBAL_FALLBACK_OLDEST

        ret["variant"] = variant.value
        return ret


def _get_emission_factor_lifecycle_and_direct(
    zone_key, dt, mode
) -> YearZoneModeEmissionFactor:
    item = {}
    item["dt"] = dt
    item["zone_key"] = zone_key
    item["mode"] = mode
    for description, data in [
        ("lifecycle", CO2EQ_PARAMETERS_LIFECYCLE),
        ("direct", CO2EQ_PARAMETERS_DIRECT),
    ]:
        result = get_zone_specific_co2eq_parameter(
            co2eq_parameters=data,
            zone_key=zone_key,
            key="emissionFactors",
            sub_key=mode,
            dt=dt,
            metadata=True,
        )
        d = {
            f"{description}_{k}": v
            for k, v in result.items()
            if k in ("datetime", "source", "value", "variant")
        }
        item = {**item, **d}
    model_obj = YearZoneModeEmissionFactor(**item)
    return model_obj


def get_emission_factors_with_metadata_all_years(
    start: int | None = None,
    end: int | None = None,
) -> list[YearZoneModeEmissionFactor]:
    start = 2015 if start is None else start
    end = datetime.now(tz=timezone.utc).year if end is None else end

    acc = []
    for zone_key in ZONES_CONFIG:
        for i in range(start, end + 1):
            dt = datetime(year=i, month=1, day=1, tzinfo=timezone.utc)
            for mode in ENERGIES:
                model_obj = _get_emission_factor_lifecycle_and_direct(
                    zone_key, dt, mode
                )
                acc.append(model_obj)

    return acc
