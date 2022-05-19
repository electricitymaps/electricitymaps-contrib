#!/usr/bin/env python3

import datetime as dt
import json
import logging
import re

import arrow
import requests
from bs4 import BeautifulSoup

from .lib import zonekey

SEARCH_DATA = re.compile(r"var gunlukUretimEgrisiData = (?P<data>.*);")
TIMEZONE = "Europe/Istanbul"
URL = "https://ytbsbilgi.teias.gov.tr/ytbsbilgi/frm_istatistikler.jsf"
EMPTY_DAY = -1

PRICE_URL = "https://seffaflik.epias.com.tr/transparency/piyasalar/" "gop/ptf.xhtml"

MAP_GENERATION = {
    "akarsu": "hydro",
    "barajli": "hydro",
    "dogalgaz": "gas",
    "lng": "gas",
    "lpg": "gas",
    "jeotermal": "geothermal",
    "taskomur": "coal",
    "asfaltitkomur": "coal",
    "linyit": "coal",
    "ithalkomur": "coal",
    "ruzgar": "wind",
    "fueloil": "oil",
    "biyokutle": "biomass",
    "nafta": "oil",
    "gunes": "solar",
    "nukleer": "nuclear",
    "kojenerasyon": "unknown",
    "motorin": "oil",
}


def as_float(prod):
    """Convert json values to float and sum all production for a further use"""
    prod["total"] = 0.0
    if isinstance(prod, dict) and "yuk" not in prod.keys():
        for prod_type, prod_val in prod.items():
            prod[prod_type] = float(prod_val)
            prod["total"] += prod[prod_type]
    return prod


def get_last_data_idx(productions) -> int:
    """
    Find index of the last production.
    :return: (int) index of the newest data or -1 if no data (empty day).
    """
    for i in range(len(productions)):
        if productions[i]["total"] < 1000:
            return i - 1
    return len(productions) - 1  # full day


def fetch_price(
    zone_key="TR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, "TR")

    r = session or requests.session()
    soup = BeautifulSoup(r.get(PRICE_URL).text, "html.parser")
    cells = soup.select(".TexAlCenter")

    # data is in td elements with class "TexAlCenter" and role "gridcell"
    data = list()
    for cell in cells:
        if cell.attrs.get("role", "") != "gridcell":
            continue
        data.append(cell.text)

    dates = [
        dt.datetime.strptime(val, "%d/%m/%Y").date()
        for i, val in enumerate(data)
        if i % 5 == 0
    ]
    times = [
        dt.datetime.strptime(val, "%H:%M").time()
        for i, val in enumerate(data)
        if i % 5 == 1
    ]
    prices = [float(val.replace(",", ".")) for i, val in enumerate(data) if i % 5 == 2]

    datapoints = [
        {
            "zoneKey": "TR",
            "currency": "TRY",
            "datetime": arrow.get(dt.datetime.combine(date, time))
            .to("Europe/Istanbul")
            .datetime,
            "price": price,
            "source": "epias.com.tr",
        }
        for date, time, price in zip(dates, times, prices)
    ]
    return datapoints


def fetch_production(
    zone_key="TR", session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    session = (
        None  # Explicitely make a new session to avoid caching from their server...
    )
    r = session or requests.session()
    tr_datetime = arrow.now().to("Europe/Istanbul").floor("day")
    response = r.get(URL, verify=False)
    str_data = re.search(SEARCH_DATA, response.text)

    production_by_hour = []
    if str_data:
        productions = json.loads(str_data.group("data"), object_hook=as_float)
        last_data_index = get_last_data_idx(productions)
        valid_production = productions[: last_data_index + 1]
        if last_data_index != EMPTY_DAY:
            for datapoint in valid_production:
                data = {
                    "zoneKey": zone_key,
                    "production": {},
                    "storage": {},
                    "source": "ytbs.teias.gov.tr",
                    "datetime": None,
                }
                data["production"] = dict(
                    zip(MAP_GENERATION.values(), [0] * len(MAP_GENERATION))
                )
                for prod_type, prod_val in datapoint.items():
                    if prod_type in MAP_GENERATION.keys():
                        data["production"][MAP_GENERATION[prod_type]] += prod_val
                    elif prod_type not in ["total", "uluslarasi", "saat"]:
                        logger.warning(
                            "Warning: %s (%d) is missing in mapping!"
                            % (prod_type, prod_val)
                        )

                try:
                    data["datetime"] = tr_datetime.replace(
                        hour=int(datapoint["saat"])
                    ).datetime
                except ValueError:
                    # 24 is not a valid hour!
                    data["datetime"] = tr_datetime.datetime

                production_by_hour.append(data)
    else:
        raise Exception("Extracted data was None")

    return production_by_hour


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
