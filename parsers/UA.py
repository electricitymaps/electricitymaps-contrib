#!/usr/bin/env python3

import http.client
import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
import dateutil

"""
tec - same as `tes` but also working as central heater,
      main fuel is gas, in critical situations - black oil
gesgaes - hydro run of river and poundage
consumptiongaespump - hydro pumped storage
vde - renewable sources - mostly wind at nighttimes and solar peaks during the day

"""
MAP_GENERATION = {
    "aes": "nuclear",
    "tec": "gas",
    "tes": "coal",
    "vde": "unknown",
    "biomass": "biomass",
    "gesgaes": "hydro",
    "solar": "solar",
    "wind": "wind",
    "oil": "oil",
    "geothermal": "geothermal",
}

MAP_STORAGE = {
    "consumptiongaespump": "hydro",
}

tz = "Europe/Kiev"


def fetch_production(
    zone_key: str = "UA",
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = []
    today = arrow.now(tz=tz).format("DD.MM.YYYY")

    conn = http.client.HTTPSConnection("ua.energy")
    payload = f"action=get_data_oes&report_date={today}&type=day"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "PostmanRuntime/7.32.3",
    }
    conn.request("POST", "/wp-admin/admin-ajax.php", payload, headers)
    res = conn.getresponse()
    response = json.loads(res.read().decode("utf-8"))

    for serie in response:
        row = {
            "zoneKey": zone_key,
            "production": {},
            "storage": {},
            "source": "ua.energy",
        }

        # Storage
        if "consumptiongaespump" in serie:
            row["storage"]["hydro"] = serie["consumptiongaespump"] * -1

        # Production
        for k, v in MAP_GENERATION.items():
            if k in serie:
                row["production"][v] = serie[k]
            else:
                row["production"][v] = 0.0

        # Date
        # For some reason, every hour returned normally as string, except for 12 AM
        if serie["hour"] == 24:
            serie["hour"] = "24:00"

        date = arrow.get("%s %s" % (today, serie["hour"]), "DD.MM.YYYY HH:mm")
        row["datetime"] = date.replace(tzinfo=dateutil.tz.gettz(tz)).datetime

        data.append(row)
    return data


if __name__ == "__main__":
    print(fetch_production())
