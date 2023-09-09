#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from json import loads
from logging import Logger, getLogger
from typing import Dict, List, Optional

from arrow import get, utcnow

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

#    Zone name Cheat Sheet

#    ZoneKey("ES"): "IberianPeninsula"
#    ZoneKey("ES-CE"): "Ceuta"
#    ZoneKey("ES-CN-FVLZ"): "LanzaroteFuerteventura"
#    ZoneKey("ES-CN-GC"): "GranCanaria"
#    ZoneKey("ES-CN-HI"): "ElHierro"
#    ZoneKey("ES-CN-IG"): "Gomera"
#    ZoneKey("ES-CN-LP"): "LaPalma"
#    ZoneKey("ES-CN-TE"): "Tenerife"
#    ZoneKey("ES-IB-FO"): "Formentera"
#    ZoneKey("ES-IB-IZ"): "Ibiza"
#    ZoneKey("ES-IB-MA"): "Mallorca"
#    ZoneKey("ES-IB-ME"): "Menorca"
#    ZoneKey("ES-ML"): "Melilla"

PRODUCTION_PARSE_MAPPING = {
    "nuc": "nuclear",
    "die": "oil",
    "genAux": "oil",
    "gas": "gas",
    "gf": "gas",
    "eol": "wind",
    "cc": "gas",
    "vap": "oil",
    "fot": "solar",
    "sol": "solar",
    "car": "coal",
    "resid": "biomass",
    "termRenov": "unknown",
    "cogenResto": "unknown",
    "tnr": "unknown",
    "trn": "unknown",
    "otrRen": "unknown",
    "cogen": "gas",
}

EXCHANGE_PARSE_MAPPING = {
    "cb": "pe_ma",
    "icb": "pe_ma",
    "emm": "ma_me",
    "emi": "ma_ib",
    "eif": "ib_fo",
    "inter": "int",
}

API_CODE_MAPPING = {
    ZoneKey("ES"): "DEMANDAQH",
    ZoneKey("ES-CE"): "CEUTA5M",
    ZoneKey("ES-CN-FVLZ"): "LZ_FV5M",
    ZoneKey("ES-CN-GC"): "GCANARIA5M",
    ZoneKey("ES-CN-HI"): "EL_HIERRO5M",
    ZoneKey("ES-CN-IG"): "LA_GOMERA5M",
    ZoneKey("ES-CN-LP"): "LA_PALMA5M",
    ZoneKey("ES-CN-TE"): "TENERIFE5M",
    ZoneKey("ES-IB-FO"): "FORMENTERA5M",
    ZoneKey("ES-IB-IZ"): "IBIZA5M",
    ZoneKey("ES-IB-MA"): "MALLORCA5M",
    ZoneKey("ES-IB-ME"): "MENORCA5M",
    ZoneKey("ES-ML"): "MELILLA5M",
}

ZONE_MAPPING = {
    ZoneKey("ES"): "Peninsula",
    ZoneKey("ES-CE"): "Peninsula",
    ZoneKey("ES-CN-FVLZ"): "Canarias",
    ZoneKey("ES-CN-GC"): "Canarias",
    ZoneKey("ES-CN-HI"): "Canarias",
    ZoneKey("ES-CN-IG"): "Canarias",
    ZoneKey("ES-CN-LP"): "Canarias",
    ZoneKey("ES-CN-TE"): "Canarias",
    ZoneKey("ES-IB-FO"): "Baleares",
    ZoneKey("ES-IB-IZ"): "Baleares",
    ZoneKey("ES-IB-MA"): "Baleares",
    ZoneKey("ES-IB-ME"): "Baleares",
    ZoneKey("ES-ML"): "Peninsula",
}

TIMEZONES_MAPPING = {
    ZoneKey("ES"): "Europe/Madrid",
    ZoneKey("ES-CE"): "Africa/Ceuta",
    ZoneKey("ES-CN-FVLZ"): "Atlantic/Canary",
    ZoneKey("ES-CN-GC"): "Atlantic/Canary",
    ZoneKey("ES-CN-HI"): "Atlantic/Canary",
    ZoneKey("ES-CN-IG"): "Atlantic/Canary",
    ZoneKey("ES-CN-LP"): "Atlantic/Canary",
    ZoneKey("ES-CN-TE"): "Atlantic/Canary",
    ZoneKey("ES-IB-FO"): "Europe/Madrid",
    ZoneKey("ES-IB-IZ"): "Europe/Madrid",
    ZoneKey("ES-IB-MA"): "Europe/Madrid",
    ZoneKey("ES-IB-ME"): "Europe/Madrid",
    ZoneKey("ES-ML"): "Africa/Ceuta",
}

SOURCE = "demanda.ree.es"

EXCHANGE_FUNCTION_MAP: Dict[ZoneKey, ZoneKey] = {
    ZoneKey("ES->ES-IB-MA"): ZoneKey("ES-IB-MA"),
    ZoneKey("ES-IB-IZ->ES-IB-MA"): ZoneKey("ES-IB-MA"),
    ZoneKey("ES-IB-FO->ES-IB-IZ"): ZoneKey("ES-IB-FO"),
    ZoneKey("ES-IB-MA->ES-IB-ME"): ZoneKey("ES-IB-MA"),
}


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Optional[Session],
    target_datetime: Optional[datetime],
):
    """Raise an exception if the parameters are not valid for this parser."""
    if "->" not in zone_key and zone_key not in ZONE_MAPPING.keys():
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


def fetch_data_ree(
    zone_key: ZoneKey, session: Session, target_datetime: Optional[datetime], tz: str
) -> Dict:
    if target_datetime is None:
        date = utcnow().to(tz).format("YYYY-MM-DD")
    else:
        date = target_datetime.strftime("%Y-%m-%d")
    system = ZONE_MAPPING[zone_key]
    zone = API_CODE_MAPPING[zone_key]
    res = session.get(
        f"https://demanda.ree.es/WSvisionaMoviles{system}Rest/resources/demandaGeneracion{system}?curva={zone}&fecha={date}"
    )
    if not res.ok:
        raise ParserException(
            "ES.py",
            f"Failed fetching data for {zone_key}",
            zone_key,
        )
    json = loads(res.text.replace("null(", "", 1).replace(r");", "", 1))
    return json["valoresHorariosGeneracion"]


def fetch_island_data(
    zone_key: ZoneKey,
    session: Session,
    target_datetime: Optional[datetime],
):
    """Fetch data for the given zone key."""
    tz = TIMEZONES_MAPPING[zone_key]
    data = fetch_data_ree(zone_key, session, target_datetime, tz)
    responses = []
    for value in data:
        ts = value.pop("ts")
        arrow = get(f"{ts} {tz}", "YYYY-MM-DD HH:mm ZZZ")
        value["timestamp"] = arrow
        responses.append(value)
    if responses:
        return responses
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
            datetime=event["timestamp"].astimezone(timezone.utc),
            consumption=event["dem"],
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
    data_mapping = PRODUCTION_PARSE_MAPPING.copy()

    ## Production mapping override for Canary Islands
    # NOTE the LNG terminals are not built yet, so power generated by "gas" or "cc" in ES-CN domain is actually using oil.
    # Recheck this every 6 months and move to gas key if there has been a change.
    # Last checked: 2022-06-27
    if zone_key.split("-")[1] == "CN":
        data_mapping["gas"] = "oil"
        data_mapping["cc"] = "oil"

    if zone_key == "ES-IB-ME" or zone_key == "ES-IB-FO":
        data_mapping["gas"] = "oil"
    if zone_key == "ES-IB-IZ":
        data_mapping["die"] = "gas"

    island_data = fetch_island_data(zone_key, ses, target_datetime)
    productionEventList = ProductionBreakdownList(logger)
    for event in island_data:

        storage = StorageMix()
        if "hid" in event:
            storage.add_value("hydro", -event["hid"])

        timestamp = event.pop("timestamp").astimezone(timezone.utc)

        production = ProductionMix()
        for key in event:
            if key in data_mapping.keys():
                production.add_value(data_mapping[key], event[key])
            elif key not in EXCHANGE_PARSE_MAPPING and key != "dem" and key != "hid":
                logger.warning(f'Key "{key}" could not be parsed!')

        productionEventList.append(
            zoneKey=zone_key,
            datetime=timestamp,
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
    ses = session or Session()

    responses = fetch_island_data(
        EXCHANGE_FUNCTION_MAP[sorted_zone_keys],
        ses,
        target_datetime,
    )

    exchangeList = ExchangeList(logger)
    for event in responses:
        exchanges = {}
        for key in event:
            if key in EXCHANGE_PARSE_MAPPING.keys():
                exchanges[EXCHANGE_PARSE_MAPPING[key]] = event[key]
            elif key not in PRODUCTION_PARSE_MAPPING and key != "dem" and key != "hid":
                logger.warning(f'Key "{key}" could not be parsed!')

        net_flow: float
        if sorted_zone_keys == "ES-IB-MA->ES-IB-ME":
            net_flow = -1 * exchanges["ma_me"]
        elif sorted_zone_keys == "ES-IB-IZ->ES-IB-MA":
            net_flow = exchanges["ma_ib"]
        elif sorted_zone_keys == "ES-IB-FO->ES-IB-IZ":
            net_flow = -1 * exchanges["ib_fo"]
        else:
            net_flow = exchanges["pe_ma"]

        exchangeList.append(
            zoneKey=sorted_zone_keys,
            datetime=event["timestamp"].astimezone(timezone.utc),
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
