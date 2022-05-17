#!/usr/bin/env python3
# coding=utf-8

import logging

import arrow
import requests

TYPE_MAPPING = {  # Real values around midnight
    "АЕЦ": "nuclear",  # 2000
    "Кондензационни ТЕЦ": "coal",  # 1800
    "Топлофикационни ТЕЦ": "gas",  # 146
    "Заводски ТЕЦ": "gas",  # 147
    "ВЕЦ": "hydro",  # 7
    "Малки ВЕЦ": "hydro",  # 74
    "ВяЕЦ": "wind",  # 488
    "ФЕЦ": "solar",  # 0
    "Био ТЕЦ": "biomass",  # 29
    "Био ЕЦ": "biomass",  # 29
    "Товар РБ": "consumption",  # 3175
}


def fetch_production(
    zone_key="BG",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = "http://www.eso.bg/api/rabota_na_EEC_json.php"
    res = r.get(url)

    assert (
        res.status_code == 200
    ), f"Exception when fetching production for {zone_key}: error when calling url={url}"

    response = res.json()

    logger.debug(f"Raw generation breakdown: {response}")

    datapoints = []
    for row in response:
        for k in TYPE_MAPPING.keys():
            if row[0].startswith(k):
                datapoints.append((TYPE_MAPPING[k], row[1]))
                break

    production = {}
    for k, v in datapoints:
        production[k] = production.get(k, 0.0) + v

    data = {
        "zoneKey": zone_key,
        "production": production,
        "storage": {},
        "source": "eso.bg",
        "datetime": arrow.utcnow().datetime,
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
