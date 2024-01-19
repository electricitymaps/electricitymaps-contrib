#!/usr/bin/env python3

import http.client
import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey

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
    "gesgaes": "hydro",
}

MAP_STORAGE = {
    "consumptiongaespump": "hydro",
}

IGNORED_VALUES = ["hour", "consumption", "consumption_diff"]

SOURCE = "ua.energy"

TZ = ZoneInfo("Europe/Kiev")


def fetch_production(
    zone_key: ZoneKey = ZoneKey("UA"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime:
        target_datetime = target_datetime.astimezone(TZ)
    else:
        target_datetime = datetime.now(TZ)

    # We are using HTTP.client because Request returns 403 http codes.
    # TODO: Look into why requests are returning 403 http codes while HTTP.client works.
    conn = http.client.HTTPSConnection("ua.energy")
    payload = f"action=get_data_oes&report_date={target_datetime.date().strftime('%d.%m.%Y')}&type=day"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "PostmanRuntime/7.32.3",
    }
    conn.request("POST", "/wp-admin/admin-ajax.php", payload, headers)
    res = conn.getresponse()
    response = json.loads(res.read().decode("utf-8"))

    production_list = ProductionBreakdownList(logger)

    for serie in response:
        production = ProductionMix()
        storage = StorageMix()

        for mode in serie:
            # Production
            if mode in MAP_GENERATION:
                production.add_value(MAP_GENERATION[mode], serie[mode])
            # Storage
            elif mode in MAP_STORAGE:
                storage.add_value(MAP_STORAGE[mode], -serie[mode])
            # Log unknown modes
            elif mode not in IGNORED_VALUES:
                logger.warning(f"Unknown mode: {mode}")

        # Date
        # For some reason, every hour returned normally as string, except for 12 AM
        if serie["hour"] == 24:
            target_datetime = target_datetime + timedelta(days=1)
            serie["hour"] = "00:00"

        date_time = target_datetime.replace(
            hour=int(serie["hour"][:2]), minute=0, second=0, microsecond=0
        )

        production_list.append(
            zoneKey=zone_key,
            production=production,
            storage=storage,
            datetime=date_time,
            source=SOURCE,
        )

    return production_list.to_list()


if __name__ == "__main__":
    print(fetch_production())
