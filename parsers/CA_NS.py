#!/usr/bin/env python3

# The datetime library is used to handle datetimes
from datetime import datetime, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

SOURCE = "nspower.ca"


def _get_ns_info(requests_obj, logger: Logger):
    zone_key = ZoneKey("CA-NS")

    # This is based on validation logic in https://www.nspower.ca/site/renewables/assets/js/site.js
    # In practical terms, I've seen hydro production go way too high (>70%) which is way more
    # than reported capacity.
    valid_percent = {
        # The validation JS reports error when Solid Fuel (coal) is over 85%,
        # but as far as I can tell, that can actually be a valid result, I've seen it a few times.
        # Use 98% instead.
        "coal": (0, 0.98),
        "gas": (0, 0.5),
        "oil": (0, 0.5),
        "biomass": (0, 0.15),
        "hydro": (0, 0.60),
        "wind": (0, 0.55),
        "imports": (0, 0.50),
    }

    # Sanity checks: verify that reported production doesn't exceed listed capacity by a lot.
    # In particular, we've seen error cases where hydro production ends up calculated as 900 MW
    # which greatly exceeds known capacity of around 520 MW.
    valid_absolute = {
        "coal": 1300,
        "gas": 700,
        "oil": 300,
        "biomass": 100,
        "hydro": 600,
        "wind": 700,
    }

    mix_url = "https://www.nspower.ca/library/CurrentLoad/CurrentMix.json"
    mix_data = requests_obj.get(mix_url).json()

    load_url = "https://www.nspower.ca/library/CurrentLoad/CurrentLoad.json"
    load_data = requests_obj.get(load_url).json()

    # filter load_data that has a value of 0 MW
    filtered_load_data = [
        load_elem for load_elem in load_data if load_elem["Base Load"] > 0
    ]

    all_production_breakdowns = ProductionBreakdownList(logger)
    all_exchanges = ExchangeList(logger)
    for mix in mix_data:
        percent_mix = {
            "coal": mix["Solid Fuel"] / 100.0,
            "gas": (mix["HFO/Natural Gas"] + mix["LM 6000's"]) / 100.0,
            "oil": mix["CT's"] / 100.0,
            "biomass": mix["Biomass"] / 100.0,
            "hydro": mix["Hydro"] / 100.0,
            "wind": mix["Wind"] / 100.0,
            "imports": mix["Imports"] / 100.0,
        }

        # datetime is in format '/Date(1493924400000)/'
        # get the timestamp 1493924400 (cutting out last three zeros as well)
        data_timestamp = int(mix["datetime"][6:-5])
        data_date = datetime.fromtimestamp(data_timestamp, tz=timezone.utc)

        # validate
        valid = True
        for gen_type, value in percent_mix.items():
            percent_bounds = valid_percent[gen_type]
            if not (percent_bounds[0] <= value <= percent_bounds[1]):
                # skip this datapoint in the loop
                valid = False
                logger.warning(
                    f"discarding datapoint at {data_date} due to {gen_type} percentage "
                    f"out of bounds: {value}",
                    extra={"key": zone_key},
                )
        if not valid:
            # continue the outer loop, not the inner
            continue

        # in mix_data, the values are expressed as percentages,
        # and have to be multiplied by load to find the actual MW value.
        corresponding_load = [
            load_period
            for load_period in filtered_load_data
            if load_period["datetime"] == mix["datetime"]
        ]

        if not corresponding_load:
            continue

        load = corresponding_load[0]["Base Load"]
        electricity_mix = {
            gen_type: round(percent_value * load, 3)
            for gen_type, percent_value in percent_mix.items()
        }

        # validate again
        valid = True
        for gen_type, value in electricity_mix.items():
            absolute_bound = valid_absolute.get(
                gen_type
            )  # imports are not in valid_absolute
            if absolute_bound and value > absolute_bound:
                valid = False
                logger.warning(
                    f"discarding datapoint at {data_date} due to {gen_type} "
                    f"too high: {value} MW",
                    extra={"key": zone_key},
                )
        if not valid:
            # continue the outer loop, not the inner
            continue

        productionMix = ProductionMix()
        for mode in electricity_mix:
            if mode in PRODUCTION_MODES:
                productionMix.add_value(mode, electricity_mix[mode])
            else:
                all_exchanges.append(
                    zoneKey=ZoneKey("CA-NB->CA-NS"),
                    netFlow=electricity_mix["imports"],
                    datetime=data_date,
                    source=SOURCE,
                )
        all_production_breakdowns.append(
            zoneKey=zone_key,
            datetime=data_date,
            production=productionMix,
            source=SOURCE,
        )
    return all_production_breakdowns.to_list(), all_exchanges.to_list()


def fetch_production(
    zone_key: str = "CA-NS",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError(
            "This parser is unable to give information more than 24 hours in the past"
        )

    r = session or Session()

    production, imports = _get_ns_info(r, logger)

    return production


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """
    Requests the last known power exchange (in MW) between two regions.

    Note: As of early 2017, Nova Scotia only has an exchange with New Brunswick (CA-NB).
    (An exchange with Newfoundland, "Maritime Link", is scheduled to open in "late 2017").

    The API for Nova Scotia only specifies imports.
    When NS is exporting energy, the API returns 0.
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is unable to give information more than 24 hours in the past"
        )

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys != "CA-NB->CA-NS":
        raise NotImplementedError("This exchange pair is not implemented")

    requests_obj = session or Session()
    _, imports = _get_ns_info(requests_obj, logger)

    return imports


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    test_logger = getLogger()

    print("fetch_production() ->")
    pprint(fetch_production(logger=test_logger))

    print('fetch_exchange("CA-NS", "CA-NB") ->')
    pprint(fetch_exchange("CA-NS", "CA-NB", logger=test_logger))
