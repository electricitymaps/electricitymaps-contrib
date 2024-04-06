#!/usr/bin/env python3

from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

SOURCE = "tso.nbpower.com"
EXCHANGE_TO_FLOWS = {
    ZoneKey("CA-NB->CA-QC"): ["QUEBEC"],
    # all of these exports are to Maine
    # (see https://www.nbpower.com/en/about-us/our-energy/system-map/),
    # currently this is mapped to ISO-NE
    ZoneKey("CA-NB->US-NE-ISNE"): ["EMEC", "ISO-NE", "MPS"],
    ZoneKey("CA-NB->CA-NS"): ["NOVA SCOTIA"],
    ZoneKey("CA-NB->CA-PE"): ["PEI"],
}


def _get_new_brunswick_flows(requests_obj):
    """
    Gets current electricity flows in and out of New Brunswick.

    There is no reported data timestamp in the page.
    The page returns current time and says "Times at which values are sampled may vary by as much as 5 minutes."
    """

    url = "https://tso.nbpower.com/Public/en/SystemInformation_realtime.asp"
    response = requests_obj.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", attrs={"bordercolor": "#191970"})

    rows = table.find_all("tr")

    headers = rows[1].find_all("td")
    values = rows[2].find_all("td")

    flows = {
        headers[i].text.strip(): float(row.text.strip()) for i, row in enumerate(values)
    }

    return flows


def fetch_production(
    zone_key: ZoneKey = ZoneKey("CA-NB"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known production mix (in MW) of a given country."""

    """
    In this case, we are calculating the amount of electricity generated
    in New Brunswick, versus imported and exported elsewhere.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or Session()
    flows = _get_new_brunswick_flows(requests_obj)

    # nb_flows['NB Demand'] is the use of electricity in NB
    # 'EMEC', 'ISO-NE', 'MPS', 'NOVA SCOTIA', 'PEI', and 'QUEBEC'
    # are exchanges - positive for exports, negative for imports
    # Electricity generated in NB is then 'NB Demand' plus all the others

    generated = (
        flows["NB Demand"]
        + flows["EMEC"]
        + flows["ISO-NE"]
        + flows["MPS"]
        + flows["NOVA SCOTIA"]
        + flows["PEI"]
        + flows["QUEBEC"]
    )
    production = ProductionBreakdownList(logger)
    production.append(
        zoneKey=zone_key,
        # Using the current utc time because the page returns the current time.
        datetime=datetime.now(tz=timezone.utc).replace(
            minute=0, second=0, microsecond=0
        ),
        source=SOURCE,
        production=ProductionMix(
            unknown=generated,
        ),
    )

    return production.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    requests_obj = session or Session()
    flows = _get_new_brunswick_flows(requests_obj)

    # In this source, positive values are exports and negative are imports.
    # In expected result, "net" represents an export.
    # So these can be used directly.

    if sorted_zone_keys not in EXCHANGE_TO_FLOWS:
        raise NotImplementedError("This exchange pair is not implemented")
    exchanges = ExchangeList(logger)
    exchanges.append(
        zoneKey=sorted_zone_keys,
        datetime=datetime.now(tz=timezone.utc).replace(
            minute=0, second=0, microsecond=0
        ),
        source=SOURCE,
        netFlow=sum([flows[flow] for flow in EXCHANGE_TO_FLOWS[sorted_zone_keys]]),
    )

    return exchanges.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print('fetch_exchange("CA-NB", "CA-PE") ->')
    print(fetch_exchange(ZoneKey("CA-NB"), ZoneKey("CA-PE")))
