#!/usr/bin/env python3

import logging

import arrow

from .lib import web

ENDPOINT = "http://uksldc.in/real-time-data.php"

INTERCONNECTIONS = {
    "IN-UP->IN-UT": [
        {"name": "400KV MORADABAD-KASHIPUR", "direction": 1},
        {"name": "400KV KASHIPUR-BARIELY 2", "direction": -1},
        {"name": "400KV KASHIPUR-BARIELY 1", "direction": -1},
        {"name": "400 KV POHANA-MUZZAFFARNAGAR", "direction": -1},
        {"name": "220KV ROORKEE-NARA", "direction": -1},
        {"name": "220KV KHODRI-SHARANPUR2", "direction": -1},
        {"name": "220KV KHODRI-SHARANPUR1", "direction": -1},
        {"name": "220KV BAREILLY-PANTNAGAR", "direction": 1},
        {"name": "132KV SITARGANJ-DOHANA", "direction": -1},
        {"name": "132KV RAMGANGA-DHAMPUR", "direction": -1},
        {"name": "132KV MAHUAKHEDAGANJ-THAKURDWARA", "direction": -1},
        {"name": "132KV KHATIMA-PILIBHIT", "direction": -1},
    ],
    "IN-HP->IN-UT": [
        {"name": "220KV KHODRI-MAJRI", "direction": -1},
        {"name": "132KV GIRBATTAI-KULHAL", "direction": 1},
    ],
}


def get_connection(soup, connection_name):
    cells = soup.find_all("td")
    for cell in cells:
        if cell.text == connection_name:
            return float(cell.find_next_sibling().text)
    return 0


def get_datetime(soup, zone_key, logger):
    paras = soup.find_all("p")
    for para in paras:
        para_text = para.text.strip()
        if "Last Updated:" in para_text:
            datetime = arrow.get(para_text, "DD-MM-YYYY HH:mm:SS").replace(
                tzinfo="Asia/Kolkata"
            )
            return datetime.datetime

    logger.warning("Datetime could not be read from webpage.", extra={"key": zone_key})
    return None


def get_production_values(soup, zone_key, logger):
    cells = soup.find_all("td")
    for cell in cells:
        cell_text = cell.text.strip()
        if cell_text == "HYDRO Total":
            hydro_value = float(cell.find_next_sibling().text)
        elif cell_text == "GAS Total":
            gas_value = float(cell.find_next_sibling().text)

    try:
        gas_value, hydro_value
    except NameError:
        logger.warning(
            "One or more production values could not be read " "from webpage.",
            extra={"key": zone_key},
        )

    production = {"gas": gas_value, "hydro": hydro_value}

    return production


def fetch_exchange(
    zone_key1="IN-UP",
    zone_key2="IN-UT",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    soup = web.get_response_soup(zone_key1, ENDPOINT)
    datetime = get_datetime(soup, zone_key1, logger)

    sorted_zone_keys = sorted([zone_key1, zone_key2])
    sorted_zone_keys = "{}->{}".format(sorted_zone_keys[0], sorted_zone_keys[1])

    connections = INTERCONNECTIONS.get(sorted_zone_keys)
    if connections is None:
        return

    exchange_value = 0
    for connection in connections:
        connection_value = get_connection(soup, connection["name"])
        connection_value *= connection["direction"]
        exchange_value += connection_value

    data = {
        "datetime": datetime,
        "netFlow": exchange_value,
        "sortedZoneKeys": sorted_zone_keys,
        "source": "uksldc.in",
    }

    return data


def fetch_production(
    zone_key="IN-UT",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    soup = web.get_response_soup(zone_key, ENDPOINT)
    datetime = get_datetime(soup, zone_key, logger)
    production = get_production_values(soup, zone_key, logger)

    data = {
        "zoneKey": "IN-UT",
        "datetime": datetime,
        "production": production,
        "source": "uksldc.in",
    }

    return data


if __name__ == "__main__":
    print("fetch_exchange(IN-HP, IN-UT) ->")
    print(fetch_exchange("IN-HP", "IN-UT"))

    print("fetch_exchange(IN-UP, IN-UT) ->")
    print(fetch_exchange("IN-UP", "IN-UT"))

    print("fetch_production() ->")
    print(fetch_production())
