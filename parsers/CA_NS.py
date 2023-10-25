#!/usr/bin/env python3
import time
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


def _get_ns_info(
    session: Session, logger: Logger
) -> tuple[ExchangeList, ProductionBreakdownList]:
    # Request data from the endpoints until the timestamps between the two
    # arrays agree or the retry limit is reached.
    for _ in range(3):
        base_loads = session.get(LOAD_URL).json()  # Base loads in MW
        mixes = session.get(MIX_URL).json()  # Electricity mix breakdowns in %
        if all(
            base_load["datetime"] == mix["datetime"]
            for base_load, mix in zip(base_loads, mixes)
        ):
            break
        time.sleep(2)
    else:
        raise ParserException(PARSER, "source data is out of sync", ZONE_KEY)

    exchanges = ExchangeList(logger)
    production_breakdowns = ProductionBreakdownList(logger)
    # Skip the first element of each JSON array because the reported base load
    # is always 0 MW.
    for base_load, mix in zip(base_loads[1:], mixes[1:]):
        # The datetime key is in the format '/Date(1493924400000)/'; extract
        # the timestamp 1493924400 (cutting out the last three zeros as well).
        date_time = datetime.fromtimestamp(
            int(base_load["datetime"][6:-5]), tz=timezone.utc
        )

        # Ensure the provided percentages are within bounds, similarly to the
        # logic in https://www.nspower.ca/site/renewables/assets/js/site.js. In
        # practical terms, I've seen hydro production go higher than 70%, which
        # is way more than reported capacity.
        if (
            15 < mix["Biomass"]
            or 60 < mix["Hydro"]
            or 50 < mix["Imports"]
            # The validation JS reports an error when Solid Fuel (coal) is over
            # 85%, but as far as I can tell, that can actually be a valid
            # result, I've seen it a few times. Use 98% instead.
            or 98 < mix["Solid Fuel"]
            or 55 < mix["Wind"]
            # Gas
            or 50 < mix["HFO/Natural Gas"] + mix["CT's"] + mix["LM 6000's"]
        ):
            logger.warning(
                f"discarding datapoint at {date_time} because some mode's "
                f"share of the mix is infeasible: {mix}",
                extra={"key": ZONE_KEY},
            )
            continue

        load = base_load["Base Load"]

        # In this source, imports are positive. In the expected result for
        # CA-NB->CA-NS, "net" represents a flow from NB to NS, i.e., an import
        # to NS, so the value can be used directly. Note that this API only
        # specifies imports; when NS is exporting energy, the API returns 0.
        exchanges.append(
            datetime=date_time,
            netFlow=load * mix["Imports"] / 100,
            source=SOURCE,
            zoneKey=ZoneKey("CA-NB->CA-NS"),
        )

        production_mix = ProductionMix()
        production_mix.add_value("biomass", load * mix["Biomass"] / 100),
        production_mix.add_value("coal", load * mix["Solid Fuel"] / 100),
        production_mix.add_value("gas", load * mix["CT's"] / 100),
        production_mix.add_value("gas", load * mix["HFO/Natural Gas"] / 100),
        production_mix.add_value("gas", load * mix["LM 6000's"] / 100),
        production_mix.add_value("hydro", load * mix["Hydro"] / 100),
        production_mix.add_value("wind", load * mix["Wind"] / 100),
        # Sanity checks: verify that reported production doesn't exceed listed
        # capacity by a lot. In particular, we've seen error cases where hydro
        # production ends up calculated as 900 MW which greatly exceeds known
        # capacity of 418 MW.
        if (
            100 < production_mix.biomass
            or 1300 < production_mix.coal
            or 700 < production_mix.gas
            or 500 < production_mix.hydro
            or 700 < production_mix.wind
        ):
            logger.warning(
                f"discarding datapoint at {date_time} because some mode's "
                f"production is infeasible: {production_mix}",
                extra={"key": ZONE_KEY},
            )
            continue
        production_breakdowns.append(
            datetime=date_time,
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
    """
    Main method, never used by the Electricity Map backend, but handy for
    testing.
    """
    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())
    print('fetch_exchange("CA-NS", "CA-NB") ->')
    pprint(fetch_exchange("CA-NS", "CA-NB"))
