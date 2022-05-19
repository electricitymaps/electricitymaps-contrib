#!/usr/bin/env python3
# coding=utf-8

"""
Parser that uses the RTE-FRANCE API to return the following data type(s)
fetch_price method copied from FR parser.
Day-ahead Price
"""

import logging
import os
import xml.etree.ElementTree as ET
from datetime import timedelta

import arrow
import requests

from parsers.lib.config import refetch_frequency


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key, session=None, target_datetime=None, logger=logging.getLogger(__name__)
) -> list:
    if target_datetime:
        now = arrow.get(target_datetime, tz="Europe/Paris")
    else:
        now = arrow.now(tz="Europe/London")

    r = session or requests.session()
    formatted_from = now.shift(days=-1).format("DD/MM/YYYY")
    formatted_to = now.format("DD/MM/YYYY")

    url = (
        "http://www.rte-france.com/getEco2MixXml.php?type=donneesMarche&da"
        "teDeb={}&dateFin={}&mode=NORM".format(formatted_from, formatted_to)
    )
    response = r.get(url)
    obj = ET.fromstring(response.content)
    datas = {}

    for donnesMarche in obj:
        if donnesMarche.tag != "donneesMarche":
            continue

        start_date = arrow.get(
            arrow.get(donnesMarche.attrib["date"]).datetime, "Europe/Paris"
        )

        for item in donnesMarche:
            if item.get("granularite") != "Global":
                continue
            country_c = item.get("perimetre")
            if zone_key != country_c:
                continue
            value = None
            for value in item:
                if value.text == "ND":
                    continue
                period = int(value.attrib["periode"])
                datetime = start_date.shift(hours=+period).datetime
                if not datetime in datas:
                    datas[datetime] = {
                        "zoneKey": zone_key,
                        "currency": "EUR",
                        "datetime": datetime,
                        "source": "rte-france.com",
                    }
                data = datas[datetime]
                data["price"] = float(value.text)

    return list(datas.values())
