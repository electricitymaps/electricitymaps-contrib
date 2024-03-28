from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
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


def extract_exchange(raw_data, exchange) -> float | None:
    """Extracts flow value and direction for a given exchange."""
    search_value = EXCHANGE_JSON_MAPPING[exchange]

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
    zone_key1: str = "CR",
    zone_key2: str = "PA",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Gets an exchange pair from the SIEPAC system."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zones = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zones not in EXCHANGE_JSON_MAPPING:
        raise NotImplementedError("This exchange is not implemented.")

    s = session or Session()

    raw_data = s.get(EXCHANGE_URL).json()
    raw_flow = extract_exchange(raw_data, sorted_zones)
    if raw_flow is None:
        raise ValueError(f"No flow value found for exchange {sorted_zones}")

    flow = round(raw_flow, 1)
    dt = _to_local_datetime(datetime.now()).replace(minute=0)

    exchange = {
        "sortedZoneKeys": sorted_zones,
        "datetime": dt,
        "netFlow": flow,
        "source": "enteoperador.org",
    }

    return exchange


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
