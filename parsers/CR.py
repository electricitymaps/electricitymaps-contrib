from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

PARSER = "CR.py"
TIMEZONE = ZoneInfo("America/Costa_Rica")

EXCHANGE_URL = (
    "https://mapa.enteoperador.org/WebServiceScadaEORRest/webresources/generic"
)
PRODUCTION_URL = (
    "https://apps.grupoice.com/CenceWeb/data/sen/json/EnergiaHorariaFuentePlanta"
)

SPANISH_TO_ENGLISH = {
    "Bagazo": "biomass",
    "Eólica": "wind",
    "Geotérmica": "geothermal",
    "Hidroeléctrica": "hydro",
    "Solar": "solar",
    "Térmica": "oil",
}

EXCHANGE_JSON_MAPPING = {
    "CR->NI": "5SISTEMA.LT230.INTER_NET_CR.CMW.MW",
    "CR->PA": "6SISTEMA.LT230.INTER_NET_PAN.CMW.MW",
}


def _as_datetime_utc(dt: datetime) -> datetime:
    """Converts a datetime object to UTC. Assumes naive datetimes to be UTC."""
    is_naive = dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None
    if is_naive:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _parse_exchange_data(
    exchange_data: list[dict], sorted_zone_keys: str
) -> float | None:
    """Extracts flow value and direction for a given exchange."""
    exchange_name = EXCHANGE_JSON_MAPPING[sorted_zone_keys]
    net_flow = next(
        (item["value"] for item in exchange_data if item["nombre"] == exchange_name),
        None,
    )

    if net_flow is None:
        raise ValueError(f"No flow value found for exchange {sorted_zone_keys}")

    return net_flow


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    # Do not use existing session as some amount of cache is taking place
    session = Session()

    # if no target_datetime is specified, this defaults to now.
    now = datetime.now(timezone.utc)
    target_datetime = (
        now if target_datetime is None else _as_datetime_utc(target_datetime)
    )

    # the backend production API works in terms of local times
    now = now.astimezone(TIMEZONE)
    target_datetime = target_datetime.astimezone(TIMEZONE)

    # if before 01:30am on the current day then fetch previous day due to data lag.
    today = datetime.combine(now, time(), tzinfo=TIMEZONE)  # truncates to day
    if today <= target_datetime < today + timedelta(days=1, hours=30):
        target_datetime -= timedelta(days=1)

    # data availability limit found by manual trial and error
    cutoff_datetime = datetime(2017, 7, 1, tzinfo=TIMEZONE)
    if target_datetime < cutoff_datetime:
        raise ParserException(
            parser=PARSER,
            message=f"CR API does not provide data before {cutoff_datetime.isoformat()}, {target_datetime.isoformat()} was requested.",
            zone_key=zone_key,
        )

    url = f"{PRODUCTION_URL}?{target_datetime.strftime('anno=%Y&mes=%m&dia=%d')}"
    response = session.get(url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    response_payload = response.json()

    production_mixes = {}
    for hourly_item in response_payload["data"]:
        production_mode = SPANISH_TO_ENGLISH.get(hourly_item["fuente"])
        if production_mode not in PRODUCTION_MODES:
            continue

        # returned timestamps are missing timezone but are local times
        timestamp = datetime.strptime(
            hourly_item["fecha"], "%Y-%m-%d %H:%M:%S.%f"
        ).replace(tzinfo=TIMEZONE)

        production_mix = production_mixes.get(timestamp, ProductionMix())
        production_mix.add_value(production_mode, hourly_item["dato"])

        production_mixes[timestamp] = production_mix

    production_breakdown_list = ProductionBreakdownList(logger)
    for timestamp, production_mix in production_mixes.items():
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            source="grupoice.com",
            production=production_mix,
        )
    return production_breakdown_list.to_list()


def fetch_exchange(
    zone_key1: ZoneKey = ZoneKey("CR"),
    zone_key2: ZoneKey = ZoneKey("PA"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets an exchange pair from the SIEPAC system."""

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    if sorted_zone_keys not in EXCHANGE_JSON_MAPPING:
        raise ParserException(
            PARSER, "This exchange is not implemented", sorted_zone_keys
        )

    if target_datetime is not None:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse historical data",
            sorted_zone_keys,
        )

    session = session or Session()
    dt = datetime.now(TIMEZONE).replace(minute=0, second=0, microsecond=0)
    response = session.get(EXCHANGE_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching exchange error code: {response.status_code}: {response.text}",
            sorted_zone_keys,
        )

    net_flow = _parse_exchange_data(response.json(), sorted_zone_keys=sorted_zone_keys)

    exchange_list = ExchangeList(logger)
    exchange_list.append(
        zoneKey=ZoneKey(sorted_zone_keys),
        datetime=dt,
        netFlow=net_flow,
        source="enteoperador.org",
    )
    return exchange_list.to_list()
