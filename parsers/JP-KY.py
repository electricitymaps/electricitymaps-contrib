#!/usr/bin/env python3
# coding=utf-8
import datetime
import logging
import re

# The arrow library is used to handle datetimes
import arrow
import numpy as np
import pandas as pd

# The request library is used to fetch content through HTTP
import requests
from bs4 import BeautifulSoup

from . import occtonet


def fetch_production(
    zone_key="JP-KY",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    data = {
        "zoneKey": zone_key,
        "datetime": None,
        "production": {
            "biomass": 0,
            "coal": 0,
            "gas": 0,
            "hydro": None,
            "nuclear": None,
            "oil": 0,
            "solar": None,
            "wind": None,
            "geothermal": None,
            "unknown": 0,
        },
        "storage": {},
        "source": "www.kyuden.co.jp",
    }
    # url for consumption and solar
    url = "https://www.kyuden.co.jp/td_power_usages/pc.html"
    r = requests.get(url)
    r.encoding = "utf-8"
    html = r.text
    soup = BeautifulSoup(html, "lxml")
    # get hours, minutes
    ts = soup.find("p", class_="puProgressNow__time").get_text()
    hours = re.findall("[\d]+(?=時)", ts)[0]
    minutes = re.findall("(?<=時)[\d]+(?=分)", ts)[0]
    # get date
    ds = soup.find("div", class_="puChangeGraph")
    date = re.findall("(?<=chart/chart)[\d]+(?=.gif)", str(ds))[0]
    # parse datetime
    dt = "".join(
        [
            date[:4],
            "-",
            date[4:6],
            "-",
            date[6:],
            " ",
            "{0:02d}:{1:02d}".format(int(hours), int(minutes)),
        ]
    )
    dt = arrow.get(dt).replace(tzinfo="Asia/Tokyo").datetime
    data["datetime"] = dt
    # consumption
    cons = soup.find("p", class_="puProgressNow__useAmount").get_text()
    cons = re.findall(
        "(?<=使用量\xa0)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*" + "(?:[eE][-+]?\d+)?(?=万kW／)",
        cons,
    )
    cons = cons[0].replace(",", "")
    # convert from 万kW to MW
    cons = float(cons) * 10
    # solar
    solar = soup.find("td", class_="puProgressSun__num").get_text()
    # convert from 万kW to MW
    solar = float(solar) * 10

    # add nuclear power plants
    # Sendai and Genkai
    url_s = "".join(
        [
            "http://www.kyuden.co.jp/php/nuclear/sendai/rename.php?",
            "A=s_power.fdat&B=ncp_state.fdat&_=1520532401043",
        ]
    )
    url_g = "".join(
        [
            "http://www.kyuden.co.jp/php/nuclear/genkai/rename.php?",
            "A=g_power.fdat&B=ncp_state.fdat&_=1520532904073",
        ]
    )
    sendai = requests.get(url_s).text
    sendai = re.findall(
        "(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*" + "(?:[eE][-+]?\d+)?(?=&)",
        sendai,
    )
    genkai = requests.get(url_g).text
    genkai = re.findall(
        "(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*" + "(?:[eE][-+]?\d+)?(?=&)",
        genkai,
    )
    nuclear = 0
    for sendai_i in sendai:
        nuclear += float(sendai_i)
    for genkai_i in genkai:
        nuclear += float(genkai_i)
    # convert from 万kW to MW
    nuclear = nuclear * 10

    # add the exchange JP-CG->JP-KY
    exch_list = occtonet.fetch_exchange("JP-KY", "JP-CG")
    # find the nearest exchanges in time to consumption timestamp
    nearest_exchanges = sorted(exch_list, key=lambda exch: abs(exch["datetime"] - dt))
    # take the nearest exchange
    exch = nearest_exchanges[0]
    # check that consumption and exchange timestamps are within a 15 minute window
    if abs(dt - exch["datetime"]).seconds <= 900:

        generation = cons - exch["netFlow"]
        data["production"]["solar"] = solar
        data["production"]["nuclear"] = nuclear
        data["production"]["unknown"] = generation - nuclear - solar

        return data
    else:
        return []


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
