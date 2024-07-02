#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix

# This parser gets all real time interconnection flows from the
# Central American Electrical Interconnection System (SIEPAC).

# map for reference
# https://www.enteoperador.org/flujos-regionales-en-tiempo-real/

DATA_URL = "https://mapa.enteoperador.org/WebServiceScadaEORRest/webresources/generic"

TIMEZONE = ZoneInfo("America/Tegucigalpa")

JSON_MAPPING = {
    "GT->MX-OR": "2LBR.LT400.1FR2-2LBR-01A.-.MW",
    "GT->SV": "3SISTEMA.LT230.INTER_NET_GT.CMW.MW",
    "GT->HN": "4LEC.LT230.2FR4-4LEC-01B.-.MW",
    "HN->SV": "3SISTEMA.LT230.INTER_NET_HO.CMW.MW",
    "HN->NI": "5SISTEMA.LT230.INTER_NET_HN.CMW.MW",
    "CR->NI": "5SISTEMA.LT230.INTER_NET_CR.CMW.MW",
    "CR->PA": "6SISTEMA.LT230.INTER_NET_PAN.CMW.MW",
}


def floor_to_minute(dt: datetime) -> datetime:
    return dt.replace(second=0, microsecond=0)


def fetch_production(
    zone_key: ZoneKey = ZoneKey("HN"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    r = session or Session()
    response = r.get(DATA_URL).json()

    # Total production data for HN from the ENTE-data is the 57th element in the JSON ('4SISTEMA.GTOT.OSYMGENTOTR.-.MW')
    production = round(response[56]["value"], 1)

    dt = floor_to_minute(datetime.now(tz=TIMEZONE))

    production_list = ProductionBreakdownList(logger)
    production_list.append(
        zoneKey=zone_key,
        datetime=dt,
        production=ProductionMix(unknown=production),
        source="enteoperador.org",
    )

    return production_list.to_list()


def extract_exchange(raw_data, exchange) -> float | None:
    """Extracts flow value and direction for a given exchange."""
    search_value = JSON_MAPPING[exchange]

    interconnection = None
    for datapoint in raw_data:
        if datapoint["nombre"] == search_value:
            interconnection = float(datapoint["value"])

    if interconnection is None:
        return None

    # positive and negative flow directions do not always correspond to EM ordering of exchanges
    if exchange in ["GT->SV", "GT->HN", "HN->SV", "CR->NI", "HN->NI"]:
        interconnection *= -1

    return interconnection


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets an exchange pair from the SIEPAC system."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zones = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zones not in JSON_MAPPING:
        raise NotImplementedError("This exchange is not implemented.")

    s = session or Session()

    raw_data = s.get(DATA_URL).json()
    flow = round(extract_exchange(raw_data, sorted_zones), 1)
    dt = floor_to_minute(datetime.now(tz=TIMEZONE))

    exchanges = ExchangeList(logger)
    exchanges.append(
        zoneKey=ZoneKey(sorted_zones),
        datetime=dt,
        netFlow=flow,
        source="enteoperador.org",
    )

    return exchanges.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production(HN) ->")
    print(fetch_production())
    print("fetch_exchange(CR, PA) ->")
    print(fetch_exchange("CR", "PA"))
    print("fetch_exchange(CR, NI) ->")
    print(fetch_exchange("CR", "NI"))
    print("fetch_exchange(HN, NI) ->")
    print(fetch_exchange("HN", "NI"))
    print("fetch_exchange(GT, MX) ->")
    print(fetch_exchange("GT", "MX"))
    print("fetch_exchange(GT, SV) ->")
    print(fetch_exchange("GT", "SV"))
    print("fetch_exchange(GT, HN) ->")
    print(fetch_exchange("GT", "HN"))
    print("fetch_exchange(HN, SV) ->")
    print(fetch_exchange("HN", "SV"))
