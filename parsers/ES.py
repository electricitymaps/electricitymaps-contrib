#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Callable, Dict, List, Optional

# package "ree" is used to parse data from www.ree.es
# maintained on github by @hectorespert at https://github.com/hectorespert/ree
from ree import (
    Ceuta,
    ElHierro,
    Formentera,
    Gomera,
    GranCanaria,
    IberianPeninsula,
    Ibiza,
    LanzaroteFuerteventura,
    LaPalma,
    Mallorca,
    Melilla,
    Menorca,
    Response,
    Tenerife,
)

# The request library is used to fetch content through HTTP
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey

from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

SOURCE = "demanda.ree.es"


ZONE_FUNCTION_MAP: Dict[ZoneKey, Callable] = {
    ZoneKey("ES"): IberianPeninsula,
    ZoneKey("ES-CE"): Ceuta,
    ZoneKey("ES-CN-FVLZ"): LanzaroteFuerteventura,
    ZoneKey("ES-CN-GC"): GranCanaria,
    ZoneKey("ES-CN-HI"): ElHierro,
    ZoneKey("ES-CN-IG"): Gomera,
    ZoneKey("ES-CN-LP"): LaPalma,
    ZoneKey("ES-CN-TE"): Tenerife,
    ZoneKey("ES-IB-FO"): Formentera,
    ZoneKey("ES-IB-IZ"): Ibiza,
    ZoneKey("ES-IB-MA"): Mallorca,
    ZoneKey("ES-IB-ME"): Menorca,
    ZoneKey("ES-ML"): Melilla,
}

EXCHANGE_FUNCTION_MAP: Dict[str, Callable] = {
    "ES->ES-IB-MA": Mallorca,
    "ES-IB-IZ->ES-IB-MA": Mallorca,
    "ES-IB-FO->ES-IB-IZ": Formentera,
    "ES-IB-MA->ES-IB-ME": Mallorca,
}

# dict of REE production types to Electricity Maps production types
PRODUCTION_MAPPING = {
    "carbon": "coal",
    "combined": "gas",
    "diesel": "oil",
    "gas": "gas",
    "hydraulic": "hydro",
    "nuclear": "nuclear",
    "other": "unknown",
    "solar": "solar",
    "vapor": "oil",
    "waste": "biomass",
    "wind": "wind",
}


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Optional[Session],
    target_datetime: Optional[datetime],
):
    """Raise an exception if the parameters are not valid for this parser."""
    if "->" not in zone_key and zone_key not in ZONE_FUNCTION_MAP.keys():
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
            zone_key,
        )
    elif "->" in zone_key and zone_key not in EXCHANGE_FUNCTION_MAP.keys():
        zone_key1, zone_key2 = zone_key.split("->")
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data between {zone_key1} and {zone_key2}.",
            zone_key,
        )
    if session is not None and not isinstance(session, Session):
        raise ParserException(
            "ES.py",
            f"Invalid session: {session}",
            zone_key,
        )
    if target_datetime is not None and not isinstance(target_datetime, datetime):
        raise ParserException(
            "ES.py",
            f"Invalid target_datetime: {target_datetime}",
            zone_key,
        )


def fetch_island_data(
    zone_key: ZoneKey, session: Session, target_datetime: Optional[datetime]
) -> List[Response]:
    """Fetch data for the given zone key."""
    if target_datetime is None:
        date = target_datetime
    else:
        date = target_datetime.strftime("%Y-%m-%d")

    data: List[Response] = ZONE_FUNCTION_MAP[zone_key](session).get_all(date)
    if data:
        return data
    else:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    check_valid_parameters(zone_key, session, target_datetime)

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses, target_datetime)
    consumption = TotalConsumptionList(logger)
    for event in island_data:
        consumption.append(
            zoneKey=zone_key,
            datetime=datetime.fromtimestamp(event.timestamp).astimezone(timezone.utc),
            consumption=event.demand,
            source="demanda.ree.es",
        )
    return consumption.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    check_valid_parameters(zone_key, session, target_datetime)
    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses, target_datetime)
    productionEventList = ProductionBreakdownList(logger)

    for event in island_data:
        production = ProductionMix()
        storage = StorageMix()

        for mode in PRODUCTION_MAPPING.keys():
            if mode in event.__dir__():
                value = getattr(event, mode)
                ## Production mapping override for Canary Islands
                # NOTE the LNG terminals are not built yet, so power generated by "gas" or "combined" in ES-CN domain is actually using oil.
                # Recheck this every 6 months and move to gas key if there has been a change.
                # Last checked: 2022-06-27
                fuel_mapping = PRODUCTION_MAPPING
                if zone_key.split("-")[1] == "CN":
                    fuel_mapping = {
                        **PRODUCTION_MAPPING,
                        "gas": "oil",
                        "combined": "oil",
                    }
                    # Reset gas to 0, as it is now oil, normally this should be skipped or set to None but to conform to how REE does it, we set it to 0
                    # We should aim to change this upstream in the future to make it uniform with other parsers going forward.
                    production.gas = 0
                production.add_value(fuel_mapping[mode], value, True)
                # Zone specific override for El Hierro
                # Hydro response is hydro storage, not hydro production
                if zone_key == "ES-CN-HI" and mode == "hydraulic":
                    storage.hydro = -value
                    production.hydro = 0

        productionEventList.append(
            zoneKey=zone_key,
            datetime=datetime.fromtimestamp(event.timestamp).astimezone(timezone.utc),
            production=production,
            storage=storage,
            source="demanda.ree.es",
        )

    return productionEventList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    check_valid_parameters(sorted_zone_keys, session, target_datetime)

    if isinstance(target_datetime, datetime):
        date = target_datetime.strftime("%Y-%m-%d")
    else:
        date = target_datetime

    ses = session or Session()

    responses: List[Response] = EXCHANGE_FUNCTION_MAP[sorted_zone_keys](ses).get_all(
        date
    )

    exchangeList = ExchangeList(logger)
    for response in responses:
        net_flow: float
        if sorted_zone_keys == "ES-IB-MA->ES-IB-ME":
            net_flow = -1 * response.link["ma_me"]
        elif sorted_zone_keys == "ES-IB-IZ->ES-IB-MA":
            net_flow = response.link["ma_ib"]
        elif sorted_zone_keys == "ES-IB-FO->ES-IB-IZ":
            net_flow = -1 * response.link["ib_fo"]
        else:
            net_flow = response.link["pe_ma"]

        exchangeList.append(
            zoneKey=sorted_zone_keys,
            datetime=datetime.fromtimestamp(response.timestamp).astimezone(
                timezone.utc
            ),
            netFlow=net_flow,
            source="demanda.ree.es",
        )

    return exchangeList.to_list()


if __name__ == "__main__":
    # Spain
    print("fetch_consumption(ES)")
    print(fetch_consumption(ZoneKey("ES")))
    print("fetch_production(ES)")
    print(fetch_production(ZoneKey("ES")))

    # Autonomous cities
    print("fetch_consumption(ES-CE)")
    print(fetch_consumption(ZoneKey("ES-CE")))
    print("fetch_production(ES-CE)")
    print(fetch_production(ZoneKey("ES-CE")))
    print("fetch_consumption(ES-ML)")
    print(fetch_consumption(ZoneKey("ES-ML")))
    print("fetch_production(ES-ML)")
    print(fetch_production(ZoneKey("ES-ML")))

    # Canary Islands
    print("fetch_consumption(ES-CN-FVLZ)")
    print(fetch_consumption(ZoneKey("ES-CN-FVLZ")))
    print("fetch_production(ES-CN-FVLZ)")
    print(fetch_production(ZoneKey("ES-CN-FVLZ")))
    print("fetch_consumption(ES-CN-GC)")
    print(fetch_consumption(ZoneKey("ES-CN-GC")))
    print("fetch_production(ES-CN-GC)")
    print(fetch_production(ZoneKey("ES-CN-GC")))
    print("fetch_consumption(ES-CN-IG)")
    print(fetch_consumption(ZoneKey("ES-CN-IG")))
    print("fetch_production(ES-CN-IG)")
    print(fetch_production(ZoneKey("ES-CN-IG")))
    print("fetch_consumption(ES-CN-LP)")
    print(fetch_consumption(ZoneKey("ES-CN-LP")))
    print("fetch_production(ES-CN-LP)")
    print(fetch_production(ZoneKey("ES-CN-LP")))
    print("fetch_consumption(ES-CN-TE)")
    print(fetch_consumption(ZoneKey("ES-CN-TE")))
    print("fetch_production(ES-CN-TE)")
    print(fetch_production(ZoneKey("ES-CN-TE")))
    print("fetch_consumption(ES-CN-HI)")
    print(fetch_consumption(ZoneKey("ES-CN-HI")))
    print("fetch_production(ES-CN-HI)")
    print(fetch_production(ZoneKey("ES-CN-HI")))

    # Balearic Islands
    print("fetch_consumption(ES-IB-FO)")
    print(fetch_consumption(ZoneKey("ES-IB-FO")))
    print("fetch_production(ES-IB-FO)")
    print(fetch_production(ZoneKey("ES-IB-FO")))
    print("fetch_consumption(ES-IB-IZ)")
    print(fetch_consumption(ZoneKey("ES-IB-IZ")))
    print("fetch_production(ES-IB-IZ)")
    print(fetch_production(ZoneKey("ES-IB-IZ")))
    print("fetch_consumption(ES-IB-MA)")
    print(fetch_consumption(ZoneKey("ES-IB-MA")))
    print("fetch_production(ES-IB-MA)")
    print(fetch_production(ZoneKey("ES-IB-MA")))
    print("fetch_consumption(ES-IB-ME)")
    print(fetch_consumption(ZoneKey("ES-IB-ME")))
    print("fetch_production(ES-IB-ME)")
    print(fetch_production(ZoneKey("ES-IB-ME")))

    # Exchanges
    print("fetch_exchange(ES, ES-IB-MA)")
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("ES-IB-MA")))
    print("fetch_exchange(ES-IB-MA, ES-IB-ME)")
    print(fetch_exchange(ZoneKey("ES-IB-MA"), ZoneKey("ES-IB-ME")))
    print("fetch_exchange(ES-IB-MA, ES-IB-IZ)")
    print(fetch_exchange(ZoneKey("ES-IB-MA"), ZoneKey("ES-IB-IZ")))
    print("fetch_exchange(ES-IB-IZ, ES-IB-FO)")
    print(fetch_exchange(ZoneKey("ES-IB-IZ"), ZoneKey("ES-IB-FO")))
