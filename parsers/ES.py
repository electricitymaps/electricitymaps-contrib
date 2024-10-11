#!/usr/bin/env python3

from datetime import datetime, timedelta
from json import loads
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

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
    "cogen": "unknown",
}

EXCHANGE_PARSE_MAPPING = {
    "cb": "pe_ma",
    "icb": "pe_ma",
    "emm": "ma_me",
    "emi": "ma_ib",
    "eif": "ib_fo",
    "inter": "int",
}

ZONE_MAPPING = {
    ZoneKey("ES"): {
        "API_CODE": "DEMANDAQH",
        "SYSTEM": "Peninsula",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-CE"): {
        "API_CODE": "CEUTA5M",
        "SYSTEM": "Peninsula",
        "TZ": "Africa/Ceuta",
    },
    ZoneKey("ES-CN-FVLZ"): {
        "API_CODE": "LZ_FV5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-GC"): {
        "API_CODE": "GCANARIA5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-HI"): {
        "API_CODE": "EL_HIERRO5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-IG"): {
        "API_CODE": "LA_GOMERA5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-LP"): {
        "API_CODE": "LA_PALMA5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-CN-TE"): {
        "API_CODE": "TENERIFE5M",
        "SYSTEM": "Canarias",
        "TZ": "Atlantic/Canary",
    },
    ZoneKey("ES-IB-FO"): {
        "API_CODE": "FORMENTERA5M",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-IZ"): {
        "API_CODE": "IBIZA5M",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-MA"): {
        "API_CODE": "MALLORCA5M",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-IB-ME"): {
        "API_CODE": "MENORCA5M",
        "SYSTEM": "Baleares",
        "TZ": "Europe/Madrid",
    },
    ZoneKey("ES-ML"): {
        "API_CODE": "MELILLA5M",
        "SYSTEM": "Peninsula",
        "TZ": "Africa/Ceuta",
    },
}

SOURCE = "demanda.ree.es"

EXCHANGE_FUNCTION_MAP: dict[ZoneKey, ZoneKey] = {
    ZoneKey("ES->ES-IB-MA"): ZoneKey("ES-IB-MA"),
    ZoneKey("ES-IB-IZ->ES-IB-MA"): ZoneKey("ES-IB-MA"),
    ZoneKey("ES-IB-FO->ES-IB-IZ"): ZoneKey("ES-IB-FO"),
    ZoneKey("ES-IB-MA->ES-IB-ME"): ZoneKey("ES-IB-MA"),
}


def check_valid_parameters(
    zone_key: ZoneKey,
    session: Session | None,
    target_datetime: datetime | None,
):
    """Raise an exception if the parameters are not valid for this parser."""
    if "->" not in zone_key and zone_key not in ZONE_MAPPING:
        raise ParserException(
            "ES.py",
            f"This parser cannot parse data for zone: {zone_key}",
            zone_key,
        )
    elif "->" in zone_key and zone_key not in EXCHANGE_FUNCTION_MAP:
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


def check_known_key(key: str, logger: Logger):
    """Check if the given key is already known and log a warning if not."""
    if (
        key not in EXCHANGE_PARSE_MAPPING
        and key not in PRODUCTION_PARSE_MAPPING
        and key not in {"dem", "hid", "ts"}
    ):
        logger.warning(f'Key "{key}" could not be parsed!')


def get_ree_data(
    zone_key: ZoneKey, session: Session, target_datetime: datetime | None, tz: str
) -> dict:
    if target_datetime is None:
        date = datetime.now(tz=ZoneInfo(tz)).strftime("%Y-%m-%d")
    else:
        date = target_datetime.strftime("%Y-%m-%d")
    system = ZONE_MAPPING[zone_key]["SYSTEM"]
    zone = ZONE_MAPPING[zone_key]["API_CODE"]
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


# Parses the date. In DST end days, the repeated hours are distinguished using a leter, this needs to be parsed
def parse_date(str_date, tz):
    if "A" in str_date:
        index = str_date.index("A")
        new_value = (
            str_date[: index - 1] + "0" + str_date[index - 1] + str_date[index + 1 :]
        )
        # If A, we use the timezone from yesterday
        return datetime.fromisoformat(
            new_value
            + f" +0{ZoneInfo(tz).utcoffset(datetime.fromisoformat(new_value) - timedelta(days=1))}"
        )
    elif "B" in str_date:
        index = str_date.index("B")
        new_value = (
            str_date[: index - 1] + "0" + str_date[index - 1] + str_date[index + 1 :]
        )
        # If B, we use the timezone from tomorrow
        return datetime.fromisoformat(
            new_value
            + f" +0{ZoneInfo(tz).utcoffset(datetime.fromisoformat(new_value) + timedelta(days=1))}"
        )
    else:
        return datetime.fromisoformat(str_date).replace(tzinfo=ZoneInfo(tz))


def fetch_and_preprocess_data(
    zone_key: ZoneKey,
    session: Session,
    logger: Logger,
    target_datetime: datetime | None,
):
    """Fetch data for the given zone key."""
    tz = ZONE_MAPPING[zone_key]["TZ"]
    data = get_ree_data(zone_key, session, target_datetime, tz)
    for value in data:
        # Add timezone info to time object
        value["ts"] = parse_date(value["ts"], tz)

        for key in value:
            check_known_key(key, logger)
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
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    check_valid_parameters(zone_key, session, target_datetime)

    ses = session or Session()
    data = fetch_and_preprocess_data(zone_key, ses, logger, target_datetime)
    consumption = TotalConsumptionList(logger)
    for event in data:
        consumption.append(
            zoneKey=zone_key,
            datetime=event["ts"],
            consumption=event["dem"],
            source="demanda.ree.es",
        )
    return consumption.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
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

    data = fetch_and_preprocess_data(zone_key, ses, logger, target_datetime)
    productionEventList = ProductionBreakdownList(logger)
    for event in data:
        storage = StorageMix()
        if "hid" in event:
            storage.add_value("hydro", -event["hid"])

        production = ProductionMix()
        for key in event:
            if key in data_mapping:
                production.add_value(data_mapping[key], event[key])

        productionEventList.append(
            zoneKey=zone_key,
            datetime=event["ts"],
            production=production,
            storage=storage,
            source="demanda.ree.es",
        )

    return productionEventList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    check_valid_parameters(sorted_zone_keys, session, target_datetime)
    ses = session or Session()

    data = fetch_and_preprocess_data(
        EXCHANGE_FUNCTION_MAP[sorted_zone_keys],
        ses,
        logger,
        target_datetime,
    )

    exchangeList = ExchangeList(logger)
    for event in data:
        exchanges = {}
        for key in event:
            if key in EXCHANGE_PARSE_MAPPING:
                exchanges[EXCHANGE_PARSE_MAPPING[key]] = event[key]

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
            datetime=event["ts"],
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
