#!/usr/bin/env python3


from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("America/Costa_Rica")
EXCHANGE_URL = (
    "https://mapa.enteoperador.org/WebServiceScadaEORRest/webresources/generic"
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


def empty_record(zone_key: str):
    return {
        "zoneKey": zone_key,
        "capacity": {},
        "production": {},
        "storage": {},
        "source": "grupoice.com",
    }


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
    zone_key: str = "CR",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
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
            parser="CR.py",
            message=f"CR API does not provide data before {cutoff_datetime.isoformat()}, {local_datetime.isoformat()} was requested.",
            zone_key=zone_key,
        )

    # Do not use existing session as some amount of cache is taking place
    r = Session()
    day = local_datetime.strftime("%d")
    month = local_datetime.strftime("%m")
    year = local_datetime.strftime("%Y")
    url = f"https://apps.grupoice.com/CenceWeb/data/sen/json/EnergiaHorariaFuentePlanta?anno={year}&mes={month}&dia={day}"

    response = r.get(url)
    resp_data = response.json()["data"]

    results = {}
    for hourly_item in resp_data:
        if hourly_item["fuente"] == "Intercambio":
            continue
        if hourly_item["fecha"] not in results:
            results[hourly_item["fecha"]] = empty_record(zone_key)

        results[hourly_item["fecha"]]["datetime"] = _to_local_datetime(
            datetime.strptime(hourly_item["fecha"], "%Y-%m-%d %H:%M:%S.%f")
        )

        if (
            SPANISH_TO_ENGLISH[hourly_item["fuente"]]
            not in results[hourly_item["fecha"]]["production"]
        ):
            results[hourly_item["fecha"]]["production"][
                SPANISH_TO_ENGLISH[hourly_item["fuente"]]
            ] = hourly_item["dato"]
        else:
            results[hourly_item["fecha"]]["production"][
                SPANISH_TO_ENGLISH[hourly_item["fuente"]]
            ] += hourly_item["dato"]

    return [results[k] for k in sorted(results.keys())]


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

    if sorted_zones not in EXCHANGE_JSON_MAPPING.keys():
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
        "datetime": dt.datetime,
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
