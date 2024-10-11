#!/usr/bin/env python3
from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.exceptions import ParserException

# The table shown on the "Daily Report" page
# (https://www.nspower.ca/oasis/system-reports-messages/daily-report) is inside
# an iframe which refers to the following URL.
EXCHANGE_URL = (
    "https://resourcesprd-nspower.aws.silvertech.net/oasis/current_report.shtml"
)
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

    # Request data from the source. Skip the first element of each JSON array
    # because the reported base load is always 0 MW.
    session = session or Session()
    loads = {  # A lookup table mapping timestamps to base loads (in MW)
        _parse_timestamp(load["datetime"]): load["Base Load"]
        for load in session.get(LOAD_URL).json()[1:]
    }
    mixes = session.get(MIX_URL).json()[1:]  # Electricity mix breakdowns in %

    production_breakdowns = ProductionBreakdownList(logger)
    for mix in mixes:
        timestamp = _parse_timestamp(mix["datetime"])
        if timestamp not in loads:
            logger.warning(
                f"unable to find base load for {timestamp}",
                extra={"zone_key": ZONE_KEY},
            )
            continue
        load = loads[timestamp]
        if load <= 0:
            logger.warning(
                f"invalid base load of {load} MW", extra={"zone_key": ZONE_KEY}
            )
            continue

        production_mix = ProductionMix()
        production_mix.add_value("biomass", load * mix["Biomass"] / 100)
        production_mix.add_value("coal", load * mix["Solid Fuel"] / 100)
        production_mix.add_value("gas", load * mix["HFO/Natural Gas"] / 100)
        production_mix.add_value("gas", load * mix["LM 6000's"] / 100)
        production_mix.add_value("hydro", load * mix["Hydro"] / 100)
        production_mix.add_value("oil", load * mix["CT's"] / 100)
        production_mix.add_value("wind", load * mix["Wind"] / 100)
        # Sanity checks: verify that reported production doesn't exceed listed
        # capacity by a lot. In particular, we've seen error cases where hydro
        # production ends up calculated as 900 MW which greatly exceeds known
        # capacity of around 520 MW.
        if (
            (production_mix.biomass or 0) > 100
            or (production_mix.coal or 0) > 1300
            or (production_mix.gas or 0) > 700
            or (production_mix.hydro or 0) > 600
            or (production_mix.oil or 0) > 300
            or (production_mix.wind or 0) > 700
        ):
            logger.warning(
                "discarding datapoint at %s because some mode's production is "
                "infeasible: %s",
                timestamp,
                production_mix,
                extra={"key": ZONE_KEY},
            )
            continue
        production_breakdowns.append(
            datetime=timestamp,
            production=production_mix,
            source=SOURCE,
            zoneKey=ZONE_KEY,
        )

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
    """
    if target_datetime:
        raise ParserException(PARSER, "Unable to fetch historical data", ZONE_KEY)

    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))
    if sorted_zone_keys not in (ZoneKey("CA-NB->CA-NS"), ZoneKey("CA-NL-NF->CA-NS")):
        raise ParserException(PARSER, "Unimplemented exchange pair", sorted_zone_keys)

    session = session or Session()
    soup = BeautifulSoup(session.get(EXCHANGE_URL).text, "html.parser")

    # Extract the timestamp from the table header.
    try:
        timestamp = datetime.strptime(
            soup.find(string="Current System Conditions").find_next("td").em.i.string,
            "%d-%b-%y %H:%M:%S",
        ).replace(tzinfo=ZoneInfo("America/Halifax"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ParserException(
            PARSER, "unable to extract timestamp", sorted_zone_keys
        ) from error

    # Choose the appropriate exchange figure for the requested zone pair.
    try:
        exchange = (
            -float(soup.find(string="NS Export ").find_next("td").string)
            if sorted_zone_keys == ZoneKey("CA-NB->CA-NS")
            else float(soup.find(string="Maritime Link Import ").find_next("td").string)
        )
    except (AttributeError, TypeError) as error:
        raise ParserException(
            PARSER, "unable to extract exchange data", sorted_zone_keys
        ) from error

    exchanges = ExchangeList(logger)
    exchanges.append(
        datetime=timestamp,
        netFlow=exchange,
        source=SOURCE,
        zoneKey=sorted_zone_keys,
    )
    return exchanges.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.
    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())
    print('fetch_exchange("CA-NS", "CA-NB") ->')
    pprint(fetch_exchange(ZoneKey("CA-NS"), ZoneKey("CA-NB")))
    print('fetch_exchange("CA-NL-NF", "CA-NS") ->')
    pprint(fetch_exchange(ZoneKey("CA-NL-NF"), ZoneKey("CA-NS")))
