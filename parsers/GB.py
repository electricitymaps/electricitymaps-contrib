#!/usr/bin/env python3
# coding=utf-8

"""
Parser that uses the RTE-FRANCE API to return the following data type(s)
fetch_price method copied from FR parser.
Day-ahead Price
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Session

from parsers.lib.config import refetch_frequency


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    r = session or Session()

    url = ("https://www.rte-france.com/themes/swi/xml/power-market-data.xml")

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
