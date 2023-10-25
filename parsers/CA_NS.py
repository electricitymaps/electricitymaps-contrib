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
# Sanity checks: verify that reported production doesn't exceed listed capacity
# by a lot. In particular, we've seen error cases where hydro production ends
# up calculated as 900 MW which greatly exceeds known capacity of 418 MW.
MEGAWATT_LIMITS = {
    "coal": 1300,
    "gas": 700,
    "biomass": 100,
    "hydro": 500,
    "wind": 700,
}
# This is based on validation logic in
# https://www.nspower.ca/site/renewables/assets/js/site.js. In practical terms,
# I've seen hydro production go way too high (>70%) which is way more than
# reported capacity.
FRACTION_LIMITS = {
    # The validation JS reports an error when Solid Fuel (coal) is over 85%,
    # but as far as I can tell, that can actually be a valid result, I've seen
    # it a few times. Use 98% instead.
    "coal": (0, 0.98),
    "gas": (0, 0.5),
    "biomass": (0, 0.15),
    "hydro": (0, 0.60),
    "wind": (0, 0.55),
    "imports": (0, 0.50),
}
ZONE_KEY = ZoneKey("CA-NS")


def _get_ns_info(
    session: Session, logger: Logger
) -> (ExchangeList, ProductionBreakdownList):
    base_loads = session.get(LOAD_URL).json()  # Base loads in MW
    mixes_percent = session.get(MIX_URL).json()  # Electricity breakdowns in %
    if any(
        base_load["datetime"] != mix_percent["datetime"]
        for base_load, mix_percent in zip(base_loads, mixes_percent)
    ):
        raise ParserException(PARSER, "source data is out of sync", ZONE_KEY)

    exchanges = ExchangeList(logger)
    production_breakdowns = ProductionBreakdownList(logger)
    # Skip the first element of each JSON array because the reported base load
    # is always 0 MW.
    for base_load, mix_percent in zip(base_loads[1:], mixes_percent[1:]):
        # The datetime key is in the format '/Date(1493924400000)/'; extract
        # the timestamp 1493924400 (cutting out the last three zeros as well).
        date_time = datetime.fromtimestamp(
            int(base_load["datetime"][6:-5]), tz=timezone.utc
        )

        mix_fraction = {
            "coal": mix_percent["Solid Fuel"] / 100.0,
            "gas": (
                mix_percent["HFO/Natural Gas"]
                + mix_percent["CT's"]
                + mix_percent["LM 6000's"]
            )
            / 100.0,
            "biomass": mix_percent["Biomass"] / 100.0,
            "hydro": mix_percent["Hydro"] / 100.0,
            "wind": mix_percent["Wind"] / 100.0,
            "imports": mix_percent["Imports"] / 100.0,
        }

        # Ensure the fractions are within bounds.
        valid = True
        for mode, fraction in mix_fraction.items():
            lower, upper = FRACTION_LIMITS[mode]
            if not (lower <= fraction <= upper):
                valid = False
                logger.warning(
                    f"discarding datapoint at {date_time} because {mode} "
                    f"fraction is out of bounds: {fraction}",
                    extra={"key": ZONE_KEY},
                )
        if not valid:
            continue

        # Convert the mix fractions to megawatts.
        mix_megawatt = {
            mode: base_load["Base Load"] * fraction
            for mode, fraction in mix_fraction.items()
        }

        # Ensure the power values (MW) are within bounds.
        valid = True
        for mode, power in mix_megawatt.items():
            limit = MEGAWATT_LIMITS.get(mode)  # Imports are excluded.
            if limit and limit < power:
                valid = False
                logger.warning(
                    f"discarding datapoint at {date_time} because {mode} "
                    f"is too high: {power} MW",
                    extra={"key": ZONE_KEY},
                )
        if not valid:
            continue

        # In this source, imports are positive. In the expected result for
        # CA-NB->CA-NS, "net" represents a flow from NB to NS, i.e., an import
        # to NS, so the value can be used directly. Note that this API only
        # specifies imports; when NS is exporting energy, the API returns 0.
        exchanges.append(
            datetime=date_time,
            netFlow=mix_megawatt["imports"],
            source=SOURCE,
            zoneKey="CA-NB->CA-NS",
        )

        production_mix = ProductionMix()
        for mode, power in mix_megawatt.items():
            if mode != "imports":
                production_mix.add_value(mode, power)
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
