#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Callable, Dict, List, Optional

# The arrow library is used to handle datetimes
from arrow import get
from electricitymap.contrib.lib.models.event_lists import TotalConsumptionList
from electricitymap.contrib.lib.types import ZoneKey

# package "ree" is used to parse data from www.ree.es
# maintained on github by @hectorespert at https://github.com/hectorespert/ree
from ree import (
    BalearicIslands,
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

from .lib.config import refetch_frequency
from .lib.exceptions import ParserException
from .lib.validation import validate

SOURCE = "demanda.ree.es"

# Literal list of valid zone keys for this parser
SUPPORTED_ZONE_KEYS: List[ZoneKey] = [
    "ES",  # Spain
    "ES-CE",  # Ceuta
    "ES-CN-FVLZ",  # Fuerteventura/Lanzarote
    "ES-CN-GC",  # Gran Canaria
    "ES-CN-HI",  # El Hierro
    "ES-CN-IG",  # Isla de la Gomera
    "ES-CN-LP",  # La Palma
    "ES-CN-TE",  # Tenerife
    "ES-IB",  # Balearic Islands
    "ES-IB-FO",  # Formentera
    "ES-IB-IZ",  # Ibiza
    "ES-IB-MA",  # Mallorca
    "ES-IB-ME",  # Menorca
    "ES-ML",  # Melilla
]

# TODO: Update floors to be non zero.
# Minimum valid zone demand. This is used to eliminate some cases
# where generation for one or more modes is obviously missing.
ZONE_FLOORS: Dict[ZoneKey, float] = {
    "ES": 0,
    "ES-CE": 0,
    "ES-CN-FVLZ": 50,
    "ES-CN-GC": 150,
    "ES-CN-HI": 2,
    "ES-CN-IG": 3,
    "ES-CN-LP": 10,
    "ES-CN-TE": 150,
    "ES-IB": 0,
    "ES-IB-FO": 0,
    "ES-IB-IZ": 0,
    "ES-IB-MA": 0,
    "ES-IB-ME": 0,
    "ES-ML": 0,
}

ZONE_FUNCTION_MAP: Dict[ZoneKey, Callable] = {
    "ES": IberianPeninsula,
    "ES-CE": Ceuta,
    "ES-CN-FVLZ": LanzaroteFuerteventura,
    "ES-CN-GC": GranCanaria,
    "ES-CN-HI": ElHierro,
    "ES-CN-IG": Gomera,
    "ES-CN-LP": LaPalma,
    "ES-CN-TE": Tenerife,
    "ES-IB": BalearicIslands,
    "ES-IB-FO": Formentera,
    "ES-IB-IZ": Ibiza,
    "ES-IB-MA": Mallorca,
    "ES-IB-ME": Menorca,
    "ES-ML": Melilla,
}

EXCHANGE_FUNCTION_MAP: Dict[str, Callable] = {
    "ES->ES-IB": BalearicIslands,
    "ES->ES-IB-MA": Mallorca,
    "ES-IB-IZ->ES-IB-MA": Mallorca,
    "ES-IB-FO->ES-IB-IZ": Formentera,
    "ES-IB-MA->ES-IB-ME": Mallorca,
}


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: Optional[datetime],
    logger: Logger,
):
    """Raise an exception if the parameters are not valid for this parser."""
    if zone_key not in SUPPORTED_ZONE_KEYS:
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
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
    if logger is not None and not isinstance(logger, Logger):
        raise ParserException(
            "ES.py",
            f"Invalid logger: {logger}",
            zone_key,
        )


def check_valid_parameters_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session,
    target_datetime: Optional[datetime],
    logger: Logger,
):
    """Raise an exception if the parameters are not valid for this parser."""
    if zone_key1 or zone_key2 not in SUPPORTED_ZONE_KEYS:
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data between: {'->'.join(sorted([zone_key1, zone_key2]))}",
            "->".join(sorted([zone_key1, zone_key2])),
        )
    if session is not None and not isinstance(session, Session):
        raise ParserException(
            "ES.py",
            f"Invalid session: {session}",
            "->".join(sorted([zone_key1, zone_key2])),
        )
    if target_datetime is not None and not isinstance(target_datetime, datetime):
        raise ParserException(
            "ES.py",
            f"Invalid target_datetime: {target_datetime}",
            "->".join(sorted([zone_key1, zone_key2])),
        )
    if logger is not None and not isinstance(logger, Logger):
        raise ParserException(
            "ES.py",
            f"Invalid logger: {logger}",
            "->".join(sorted([zone_key1, zone_key2])),
        )


def fetch_island_data(
    zone_key: ZoneKey, session: Session, target_datetime: Optional[datetime]
) -> List[Response]:
    """Fetch data for the given zone key."""
    if target_datetime is None:
        date = target_datetime
    else:
        date = target_datetime.strftime("%Y-%m-%d")
    try:
        data: List[Response] = ZONE_FUNCTION_MAP[zone_key](session).get_all(date)
    except KeyError:
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
            zone_key,
        )
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
    check_valid_parameters(zone_key, session, target_datetime, logger)

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses, target_datetime)
    consumption = TotalConsumptionList(logger)
    for event in island_data:
        consumption.append(
            zoneKey=zone_key,
            datetime=get(event.timestamp).datetime,
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
    check_valid_parameters(zone_key, session, target_datetime, logger)

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses, target_datetime)
    data: List[Dict[str, Any]] = []

    # If we add more zones this should be turned into a map similar to ZONE_FlOORS mapping.
    if zone_key == "ES-IB":
        expected_range = {"coal": (50, 600)}
    else:
        expected_range = None

    if island_data:
        for response in island_data:
            if response.production() >= 0:
                response_data = {
                    "datetime": get(response.timestamp).datetime,
                    "production": {
                        "biomass": response.waste,
                        "coal": response.carbon,
                        "gas": round((response.gas + response.combined), 2),
                        "geothermal": 0.0,
                        "hydro": response.hydraulic,
                        "nuclear": 0.0,
                        "oil": round((response.vapor + response.diesel), 2),
                        "solar": response.solar,
                        "unknown": response.other,
                        "wind": response.wind,
                    },
                    "source": "demanda.ree.es",
                    "storage": {"hydro": 0.0, "battery": 0.0},
                    "zoneKey": zone_key,
                }

                ### Zone overrides
                # NOTE the LNG terminals are not built yet, so power generated by "gas" or "combined" in ES-CN domain is actually using oil.
                # Recheck this every 6 months and move to gas key if there has been a change.
                # Last checked: 2022-06-27
                if zone_key.split("-")[1] == "CN":
                    response_data["production"]["gas"] = 0.0
                    response_data["production"]["oil"] = round(
                        (
                            response.vapor
                            + response.diesel
                            + response.gas
                            + response.combined
                        ),
                        2,
                    )

                # Hydro response is hydro storage
                if zone_key == "ES-CN-HI":
                    response_data["production"]["hydro"] = 0.0
                    response_data["storage"]["hydro"] = -response.hydraulic

                response_data = validate(
                    response_data,
                    logger,
                    floor=ZONE_FLOORS[zone_key],
                    expected_range=expected_range,
                )

                if response_data:
                    # append if valid
                    data.append(response_data)
        return data

    else:
        raise ParserException(
            "ES.py", f"No production data returned for zone: {zone_key}", zone_key
        )


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    check_valid_parameters_exchange(
        zone_key1, zone_key2, session, target_datetime, logger
    )

    if isinstance(target_datetime, datetime):
        date = target_datetime.strftime("%Y-%m-%d")
    else:
        date = target_datetime

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    ses = session or Session()

    responses: List[Response] = EXCHANGE_FUNCTION_MAP[sorted_zone_keys](ses).get_all(
        date
    )
    if not responses:
        raise NotImplementedError(
            f'Exchange pair "{sorted_zone_keys}" is not implemented in this parser'
        )

    exchanges = []
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

        exchange = {
            "datetime": get(response.timestamp).datetime,
            "netFlow": net_flow,
            "sortedZoneKeys": sorted_zone_keys,
            "source": "demanda.ree.es",
        }

        exchanges.append(exchange)

    return exchanges


if __name__ == "__main__":
    # Spain
    print("fetch_consumption(ES)")
    print(fetch_consumption("ES"))
    print("fetch_production(ES)")
    print(fetch_production("ES"))

    # Autonomous cities
    print("fetch_consumption(ES-CE)")
    print(fetch_consumption("ES-CE"))
    print("fetch_production(ES-CE)")
    print(fetch_production("ES-CE"))
    print("fetch_consumption(ES-ML)")
    print(fetch_consumption("ES-ML"))
    print("fetch_production(ES-ML)")
    print(fetch_production("ES-ML"))

    # Canary Islands
    print("fetch_consumption(ES-CN-FVLZ)")
    print(fetch_consumption("ES-CN-FVLZ"))
    print("fetch_production(ES-CN-FVLZ)")
    print(fetch_production("ES-CN-FVLZ"))
    print("fetch_consumption(ES-CN-GC)")
    print(fetch_consumption("ES-CN-GC"))
    print("fetch_production(ES-CN-GC)")
    print(fetch_production("ES-CN-GC"))
    print("fetch_consumption(ES-CN-IG)")
    print(fetch_consumption("ES-CN-IG"))
    print("fetch_production(ES-CN-IG)")
    print(fetch_production("ES-CN-IG"))
    print("fetch_consumption(ES-CN-LP)")
    print(fetch_consumption("ES-CN-LP"))
    print("fetch_production(ES-CN-LP)")
    print(fetch_production("ES-CN-LP"))
    print("fetch_consumption(ES-CN-TE)")
    print(fetch_consumption("ES-CN-TE"))
    print("fetch_production(ES-CN-TE)")
    print(fetch_production("ES-CN-TE"))
    print("fetch_consumption(ES-CN-HI)")
    print(fetch_consumption("ES-CN-HI"))
    print("fetch_production(ES-CN-HI)")
    print(fetch_production("ES-CN-HI"))

    # Balearic Islands
    print("fetch_consumption(ES-IB)")
    print(fetch_consumption("ES-IB"))
    print("fetch_production(ES-IB)")
    print(fetch_production("ES-IB"))
    print("fetch_consumption(ES-IB-FO)")
    print(fetch_consumption("ES-IB-FO"))
    print("fetch_production(ES-IB-FO)")
    print(fetch_production("ES-IB-FO"))
    print("fetch_consumption(ES-IB-IZ)")
    print(fetch_consumption("ES-IB-IZ"))
    print("fetch_production(ES-IB-IZ)")
    print(fetch_production("ES-IB-IZ"))
    print("fetch_consumption(ES-IB-MA)")
    print(fetch_consumption("ES-IB-MA"))
    print("fetch_production(ES-IB-MA)")
    print(fetch_production("ES-IB-MA"))
    print("fetch_consumption(ES-IB-ME)")
    print(fetch_consumption("ES-IB-ME"))
    print("fetch_production(ES-IB-ME)")
    print(fetch_production("ES-IB-ME"))

    # Exchanges
    print("fetch_exchange(ES, ES-IB)")
    print(fetch_exchange("ES", "ES-IB"))
    print("fetch_exchange(ES, ES-IB-MA)")
    print(fetch_exchange("ES", "ES-IB-MA"))
    print("fetch_exchange(ES-IB-MA, ES-IB-ME)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-ME"))
    print("fetch_exchange(ES-IB-MA, ES-IB-IZ)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-IZ"))
    print("fetch_exchange(ES-IB-IZ, ES-IB-FO)")
    print(fetch_exchange("ES-IB-IZ", "ES-IB-FO"))
