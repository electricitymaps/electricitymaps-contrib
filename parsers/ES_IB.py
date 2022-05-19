#!/usr/bin/env python3

import logging

from arrow import get
from ree import BalearicIslands, Formentera, Ibiza, Mallorca, Menorca
from requests import Session

from .lib.exceptions import ParserException
from .lib.validation import validate, validate_production_diffs

# package "ree" is used to parse data from www.ree.es // maintained on github by @hectorespert


## Guess we'll need to figure these out later?! Adapted from ES-CN:

# Minimum valid zone demand. This is used to eliminate some cases
# where generation for one or more modes is obviously missing.
FLOORS = {
    "ES-IB": 0,
    "ES-IB-FO": 0,
    "ES-IB-IZ": 0,
    "ES-IB-MA": 0,
    "ES-IB-ME": 0,
}


def fetch_island_data(zone_key, session):
    if zone_key == "ES-IB-FO":
        formentera_data = Formentera(session, verify=False).get_all()
        if not formentera_data:
            raise ParserException(zone_key, "Formentera doesn't respond")
        else:
            return formentera_data
    elif zone_key == "ES-IB-IZ":
        ibiza_data = Ibiza(session, verify=False).get_all()
        if not ibiza_data:
            raise ParserException(zone_key, "Party is over, Ibiza doesn't respond")
        else:
            return ibiza_data
    elif zone_key == "ES-IB-MA":
        mallorca_data = Mallorca(session, verify=False).get_all()
        if not mallorca_data:
            raise ParserException(zone_key, "Mallorca doesn't respond")
        else:
            return mallorca_data
    elif zone_key == "ES-IB-ME":
        menorca_data = Menorca(session, verify=False).get_all()
        if not menorca_data:
            raise ParserException(zone_key, "Menorca doesn't respond")
        else:
            return menorca_data
    elif zone_key == "ES-IB":
        balearic_islands = BalearicIslands(session, verify=False).get_all()
        if not balearic_islands:
            raise ParserException(zone_key, "Balearic Islands doesn't respond")
        else:
            return balearic_islands
    else:
        raise ParserException(
            zone_key, "Can't read this country code {0}".format(zone_key)
        )


def fetch_consumption(
    zone_key, session=None, target_datetime=None, logger=None
) -> list:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []
    for response in island_data:
        response_data = {
            "zoneKey": zone_key,
            "datetime": get(response.timestamp).datetime,
            "consumption": response.demand,
            "source": "demanda.ree.es",
        }

        data.append(response_data)

    return data


def fetch_production(
    zone_key, session=None, target_datetime=None, logger=logging.getLogger(__name__)
) -> list:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []

    if zone_key == "ES-IB":
        expected_range = {"coal": (50, 600)}
    else:
        expected_range = None

    for response in island_data:
        if response.production() >= 0:
            response_data = {
                "zoneKey": zone_key,
                "datetime": get(response.timestamp).datetime,
                "production": {
                    "coal": response.carbon,
                    "gas": round(response.gas + response.combined, 2),
                    "solar": response.solar,
                    "oil": round(response.vapor + response.diesel, 2),
                    "wind": response.wind,
                    "hydro": response.hydraulic,
                    "biomass": response.waste,
                    "nuclear": 0.0,
                    "geothermal": 0.0,
                    "unknown": response.other,
                },
                "storage": {"hydro": 0.0, "battery": 0.0},
                "source": "demanda.ree.es",
            }

            response_data = validate(
                response_data,
                logger,
                floor=FLOORS[zone_key],
                expected_range=expected_range,
            )

            if response_data:
                # append if valid
                data.append(response_data)

    if len(data) > 1:
        # granularity is 10 minutes, drops points with change in coal > 100MW
        data = validate_production_diffs(data, {"coal": 150}, logger)

    return data


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    ses = session or Session()

    if sorted_zone_keys == "ES->ES-IB":
        responses = BalearicIslands(ses, verify=False).get_all()
        if not responses:
            raise ParserException("ES-IB", "No responses")
    elif (
        sorted_zone_keys == "ES->ES-IB-MA"
        or sorted_zone_keys == "ES-IB-MA->ES-IB-ME"
        or sorted_zone_keys == "ES-IB-IZ->ES-IB-MA"
    ):
        responses = Mallorca(ses, verify=False).get_all()
        if not responses:
            raise ParserException("ES-IB-MA", "No responses")
    elif sorted_zone_keys == "ES-IB-FO->ES-IB-IZ":
        responses = Formentera(ses, verify=False).get_all()
        if not responses:
            raise ParserException("ES-IB-FO", "No responses")
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    exchanges = []
    for response in responses:

        if sorted_zone_keys == "ES-IB-MA->ES-IB-ME":
            net_flow = -1 * response.link["ma_me"]
        elif sorted_zone_keys == "ES-IB-IZ->ES-IB-MA":
            net_flow = response.link["ma_ib"]
        elif sorted_zone_keys == "ES-IB-FO->ES-IB-IZ":
            net_flow = -1 * response.link["ib_fo"]
        else:
            net_flow = response.link["pe_ma"]

        exchange = {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": get(response.timestamp).datetime,
            "netFlow": net_flow,
            "source": "demanda.ree.es",
        }

        exchanges.append(exchange)

    return exchanges


if __name__ == "__main__":
    session = Session
    print("fetch_consumption(ES-IB)")
    print(fetch_consumption("ES-IB", session))

    print("fetch_production(ES-IB)")
    print(fetch_production("ES-IB", session))

    print("fetch_exchange(ES, ES-IB)")
    print(fetch_exchange("ES", "ES-IB", session))

    print("fetch_consumption(ES-IB-FO)")
    print(fetch_consumption("ES-IB-FO"))
    print("fetch_production(ES-IB-FO)")
    print(fetch_production("ES-IB-FO"))
    print("fetch_consumption(ES-IB-IZ)")
    print(fetch_consumption("ES-IB-IZ"))
    print("fetch_production(ES-IB-IZ)")
    print(fetch_production("ES-IB-IZ"))
    print("fetch_consumption(ES-IB-MA)")
    print(fetch_consumption("ES-IB-MA"))
    print("fetch_production(ES-IB-MA)")
    print(fetch_production("ES-IB-MA"))
    print("fetch_consumption(ES-IB-ME)")
    print(fetch_consumption("ES-IB-ME"))
    print("fetch_production(ES-IB-ME)")
    print(fetch_production("ES-IB-ME"))
    print("fetch_exchange(ES, ES-IB-MA)")
    print(fetch_exchange("ES", "ES-IB-MA"))
    print("fetch_exchange(ES-IB-MA, ES-IB-ME)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-ME"))
    print("fetch_exchange(ES-IB-MA, ES-IB-IZ)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-IZ"))
    print("fetch_exchange(ES-IB-IZ, ES-IB-FO)")
    print(fetch_exchange("ES-IB-IZ", "ES-IB-FO"))
