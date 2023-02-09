#!/usr/bin/env python3
# coding=utf-8


from datetime import datetime, time
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Session

TIMEZONE = "America/Costa_Rica"
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


def empty_record(zone_key: str):
    return {
        "zoneKey": zone_key,
        "capacity": {},
        "production": {},
        "storage": {},
        "source": "grupoice.com",
    }


def extract_exchange(raw_data, exchange) -> Optional[float]:
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


def fetch_production(
    zone_key: str = "CR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    # ensure we have an arrow object.
    # if no target_datetime is specified, this defaults to now.
    arw_datetime = arrow.get(target_datetime).to(TIMEZONE)

    # if before 01:30am on the current day then fetch previous day due to
    # data lag.
    today = arrow.get().to(TIMEZONE).date()
    if arw_datetime.date() == today:
        arw_datetime = (
            arw_datetime
            if arw_datetime.time() >= time(1, 30)
            else arw_datetime.shift(days=-1)
        )

    if arw_datetime < arrow.get("2012-07-01"):
        # data availability limit found by manual trial and error
        logger.error(
            "CR API does not provide data before 2012-07-01, "
            "{} was requested".format(arw_datetime),
            extra={"key": zone_key},
        )
        return None

    # Do not use existing session as some amount of cache is taking place
    r = Session()
    day = arw_datetime.format("DD")
    month = arw_datetime.format("MM")
    year = arw_datetime.format("YYYY")
    url = f"https://apps.grupoice.com/CenceWeb/data/sen/json/EnergiaHorariaFuentePlanta?anno={year}&mes={month}&dia={day}"

    response = r.get(url)
    resp_data = response.json()["data"]

    results = {}
    for hourly_item in resp_data:
        if hourly_item["fuente"] == "Intercambio":
            continue
        if hourly_item["fecha"] not in results:
            results[hourly_item["fecha"]] = empty_record(zone_key)

        results[hourly_item["fecha"]]["datetime"] = arrow.get(
            hourly_item["fecha"], tzinfo=TIMEZONE
        ).datetime

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
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
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
        raise ValueError("No flow value found for exchange {}".format(sorted_zones))

    flow = round(raw_flow, 1)
    dt = arrow.now("UTC-6").floor("minute")

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

    # print('fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z")))

    # # this should work
    # print('fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z")))

    # # this should return None
    # print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z")))

    print("fetch_exchange() ->")
    print(fetch_exchange())
