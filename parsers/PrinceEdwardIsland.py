#!/usr/bin/env python3
import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

SOURCE = "PrinceEdwardIsland.ca"
TIMEZONE = ZoneInfo("Canada/Atlantic")
# The dashboard associated with this API can be found at
# https://www.PrinceEdwardIsland.ca/en/feature/pei-wind-energy.
URL = "https://wdf.PrinceEdwardIsland.ca/api/workflow"  # API
ZONE_KEY = ZoneKey("CA-PE")


def _parse_power(text: str) -> float:
    return float(text[: text.index(" MW")])


def _get_event(session: Session):
    # Request an event from the source.
    event = session.post(
        URL,
        data=json.dumps({"featureName": "WindEnergy", "queryName": "WindEnergy"}),
        headers={"Content-Type": "application/json"},
    ).json()["data"]
    # Collect the production modes and power values into a lookup table.
    modes = dict(
        object_["data"]["header"].split(": ", maxsplit=1)
        for object_ in event
        if object_["type"] == "GaugeChart"
    )
    # Extract the timestamp.
    timestamp = datetime.strptime(
        event[-1]["data"]["text"][len("Last updated ") :], "%B %d, %Y %I:%M %p"
    ).replace(tzinfo=TIMEZONE)
    # Return a new, more convenient lookup table.
    return {
        "datetime": timestamp,
        "fossil": _parse_power(modes["Total On-Island Fossil Fuel Generation"]),
        "load": _parse_power(modes["Total On-Island Load"]),
        "wind": _parse_power(modes["Total On-Island Wind Generation"]),
    }


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""
    if zone_key != ZONE_KEY:
        raise ParserException(
            "PrinceEdwardIsland.py", "Cannot parse zone '{zone_key}'", zone_key
        )
    if target_datetime:
        raise ParserException(
            "PrinceEdwardIsland.py", "Unable to fetch historical data", ZONE_KEY
        )

    event = _get_event(session or Session())

    production_mix = ProductionMix()

    # These are oil-fueled ("heavy fuel oil" and "diesel") generators used as
    # peakers and back-up.
    production_mix.add_value("oil", event["fossil"])
    production_mix.add_value("wind", event["wind"])

    production_breakdowns = ProductionBreakdownList(logger)
    production_breakdowns.append(
        datetime=event["datetime"],
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
    """Requests the last known power exchange (in MW) between two regions."""

    sorted_zone_keys = ZoneKey("->".join(sorted((zone_key1, zone_key2))))

    if target_datetime:
        raise ParserException(
            "PrinceEdwardIsland.py", "Unable to fetch historical data", sorted_zone_keys
        )

    if sorted_zone_keys != ZoneKey("CA-NB->CA-PE"):
        raise ParserException(
            "PrinceEdwardIsland.py",
            f"The exchange pair '{sorted_zone_keys}' is not implemented",
            sorted_zone_keys,
        )

    # PEI imports most of its electricity. Everything not generated on the
    # island is imported from New Brunswick.
    #
    # In the case of wind, some is "paper-exported" even if there is a net
    # import, and the "Wind Power Exported Off Island" gauge on the dashboard
    # indicates their accounting of these exports. The dashboard says:
    #
    #   Wind Power Exported Off-Island is that portion of wind generation that
    #   is supplying contracts elsewhere. The actual electricity from this
    #   portion of wind generation may stay within PEI but is satisfying a
    #   contractual arrangement in another jurisdiction.
    #
    # We are ignoring these paper exports, as they are an accounting/legal
    # detail that doesn't actually reflect what happens on the wires. Given
    # that NB is the only interconnection with PEI, physically exporting wind
    # power to NB while simultaneously importing the balance seems unlikely.
    event = _get_event(session or Session())
    exchanges = ExchangeList(logger)
    exchanges.append(
        datetime=event["datetime"],
        # The sorted zones are CA-NB -> CA-PE, so a positive value represents
        # export from NB / import into PE.
        netFlow=event["load"] - event["fossil"] - event["wind"],
        source=SOURCE,
        zoneKey=sorted_zone_keys,
    )

    return exchanges.to_list()


if __name__ == "__main__":
    # Never used by the Electricity Map backend, but handy for testing.

    print("fetch_production() ->")
    print(fetch_production())

    print('fetch_exchange("CA-PE", "CA-NB") ->')
    print(fetch_exchange(ZoneKey("CA-PE"), ZoneKey("CA-NB")))
