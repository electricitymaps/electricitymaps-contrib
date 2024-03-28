from datetime import datetime, time, timedelta
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


def _to_local_datetime(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TIMEZONE)
    return dt.astimezone(TIMEZONE)


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
    target_datetime = target_datetime or datetime.now()
    local_datetime = _to_local_datetime(target_datetime)

    # if before 01:30am on the current day then fetch previous day due to
    # data lag.
    today = _to_local_datetime(datetime.now()).date()
    if local_datetime.date() == today:
        local_datetime = (
            local_datetime
            if local_datetime.time() >= time(1, 30)
            else local_datetime - timedelta(days=1)
        )

    cutoff_datetime = _to_local_datetime(datetime(2017, 7, 1))
    if local_datetime < cutoff_datetime:
        # data availability limit found by manual trial and error
        raise ParserException(
            parser=PARSER,
            message=f"CR API does not provide data before {cutoff_datetime.isoformat()}, {local_datetime.isoformat()} was requested.",
            zone_key=zone_key,
        )

    day = local_datetime.strftime("%d")
    month = local_datetime.strftime("%m")
    year = local_datetime.strftime("%Y")
    url = f"{PRODUCTION_URL}?anno={year}&mes={month}&dia={day}"
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

        timestamp = _to_local_datetime(
            datetime.strptime(hourly_item["fecha"], "%Y-%m-%d %H:%M:%S.%f")
        )
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
    dt = _to_local_datetime(datetime.now()).replace(minute=0)
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


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())

    # print('fetch_production(target_datetime=datetime.strptime("2018-03-13T12:00Z", "%Y-%m-%dT%H:%MZ") ->')
    # pprint(fetch_production(target_datetime=datetime.strptime("2018-03-13T12:00Z", "%Y-%m-%dT%H:%MZ")))

    # # this should work
    # print('fetch_production(target_datetime=datetime.strptime("2018-03-13T12:00Z", "%Y-%m-%dT%H:%MZ") ->')
    # pprint(fetch_production(target_datetime=datetime.strptime("2018-03-13T12:00Z", "%Y-%m-%dT%H:%MZ")))

    # # this should return None
    # print('fetch_production(target_datetime=datetime.strptime("2007-03-13T12:00Z", "%Y-%m-%dT%H:%MZ") ->')
    # pprint(fetch_production(target_datetime=datetime.strptime("2007-03-13T12:00Z", "%Y-%m-%dT%H:%MZ")))

    print("fetch_exchange() ->")
    print(fetch_exchange())
