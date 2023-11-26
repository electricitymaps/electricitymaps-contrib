#!/usr/bin/env python3
from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.exceptions import ParserException

LOAD_URL = "https://www.nspower.ca/library/CurrentLoad/CurrentLoad.json"
MIX_URL = "https://www.nspower.ca/library/CurrentLoad/CurrentMix.json"
PARSER = "CA_NS.py"
SOURCE = "nspower.ca"
ZONE_KEY = ZoneKey("CA-NS")


def _parse_timestamp(timestamp: str) -> datetime:
    """
    Construct a datetime object from a date string formatted as, e.g.,
    "/Date(1493924400000)/" by extracting the Unix timestamp 1493924400. Note
    that the three trailing zeros are cut out as well).
    """
    return datetime.fromtimestamp(int(timestamp[6:-5]), tz=timezone.utc)


def _get_ns_info(
    session: Session, logger: Logger
) -> tuple[ExchangeList, ProductionBreakdownList]:
    # Request data from the source. Skip the first element of each JSON array
    # because the reported base load is always 0 MW.
    loads = {  # Lookup table mapping timestamps to base loads (in MW)
        _parse_timestamp(load["datetime"]): load["Base Load"]
        for load in session.get(LOAD_URL).json()[1:]
    }
    mixes = session.get(MIX_URL).json()[1:]  # Electricity mix breakdowns in %

    exchanges = ExchangeList(logger)
    production_breakdowns = ProductionBreakdownList(logger)
    for mix in mixes:
        timestamp = _parse_timestamp(mix["datetime"])
        if timestamp in loads:
            load = loads[timestamp]
        else:
            # If a base load corresponding with this timestamp is not found,
            # assume 1244 MW based on the average yearly electricity available
            # for use in 2014 and 2015 (Statistics Canada table 127-0008 for
            # Nova Scotia).
            load = 1244
            logger.warning(
                f"unable to find load for {timestamp}; assuming 1244 MW",
                extra={"key": ZONE_KEY},
            )

        # In this source, imports are positive. In the expected result for
        # CA-NB->CA-NS, "net" represents a flow from NB to NS, i.e., an import
        # to NS, so the value can be used directly.
        #
        # NOTE: this API only specifies imports; when NS is exporting energy,
        # the API returns 0.
        #
        # TODO: the Newfoundland and Labrador / Novia Scotia interconnect is
        # now live, so this exchange logic should be revisited.
        exchanges.append(
            datetime=timestamp,
            netFlow=load * mix["Imports"] / 100,
            source=SOURCE,
            zoneKey=ZoneKey("CA-NB->CA-NS"),
        )

        production_mix = ProductionMix()
        production_mix.add_value("biomass", load * mix["Biomass"] / 100)
        production_mix.add_value("coal", load * mix["Solid Fuel"] / 100)
        production_mix.add_value("gas", load * mix["CT's"] / 100)
        production_mix.add_value("gas", load * mix["HFO/Natural Gas"] / 100)
        production_mix.add_value("gas", load * mix["LM 6000's"] / 100)
        production_mix.add_value("hydro", load * mix["Hydro"] / 100)
        production_mix.add_value("wind", load * mix["Wind"] / 100)
        # Sanity checks: verify that reported production doesn't exceed listed
        # capacity by a lot. In particular, we've seen error cases where hydro
        # production ends up calculated as 900 MW which greatly exceeds known
        # capacity of 418 MW.
        if (
            100 < (production_mix.biomass or 0)
            or 1300 < (production_mix.coal or 0)
            or 700 < (production_mix.gas or 0)
            or 500 < (production_mix.hydro or 0)
            or 700 < (production_mix.wind or 0)
        ):
            logger.warning(
                f"discarding datapoint at {timestamp} because some mode's "
                f"production is infeasible: {production_mix}",
                extra={"key": ZONE_KEY},
            )
            continue
        production_breakdowns.append(
            datetime=timestamp,
            production=production_mix,
            source=SOURCE,
            zoneKey=ZONE_KEY,
        )

    return exchanges, production_breakdowns


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise ParserException(PARSER, "Unable to fetch historical data", zone_key)

    if zone_key != ZONE_KEY:
        raise ParserException(PARSER, f"Cannot parse zone '{zone_key}'", zone_key)

    _, production_breakdowns = _get_ns_info(session or Session(), logger)
    return production_breakdowns.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Requests the last known power exchange (in MW) between two regions.

    Note: As of early 2017, Nova Scotia only has an exchange with New Brunswick
    (CA-NB). (An exchange with Newfoundland, "Maritime Link", is scheduled to
    open in "late 2017").

    The API for Nova Scotia only specifies imports. When NS is exporting
    energy, the API returns 0.
    """
    if target_datetime:
        raise ParserException(PARSER, "Unable to fetch historical data", ZONE_KEY)

    sorted_zone_keys = "->".join(sorted((zone_key1, zone_key2)))
    if sorted_zone_keys != "CA-NB->CA-NS":
        raise ParserException(PARSER, "Unimplemented exchange pair", sorted_zone_keys)

    exchanges, _ = _get_ns_info(session or Session(), logger)
    return exchanges.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.
    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())
    print('fetch_exchange("CA-NS", "CA-NB") ->')
    pprint(fetch_exchange("CA-NS", "CA-NB"))
