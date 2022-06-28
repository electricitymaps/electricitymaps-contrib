#!/usr/bin/env python3

import datetime
import logging

# The arrow library is used to handle datetimes
from arrow import get

# package "ree" is used to parse data from www.ree.es
# maintained on github by @hectorespert at https://github.com/hectorespert/ree
from ree import (
    BalearicIslands,
    ElHierro,
    Formentera,
    Gomera,
    GranCanaria,
    Ibiza,
    LanzaroteFuerteventura,
    LaPalma,
    Mallorca,
    Menorca,
    Tenerife,
)

# The request library is used to fetch content through HTTP
from requests import Session

from .lib.exceptions import ParserException
from .lib.validation import validate

# Minimum valid zone demand. This is used to eliminate some cases
# where generation for one or more modes is obviously missing.
FLOORS: dict[str, int] = {
    "ES-CN-FVLZ": 50,
    "ES-CN-GC": 150,
    "ES-CN-IG": 3,
    "ES-CN-LP": 10,
    "ES-CN-TE": 150,
    "ES-CN-HI": 2,
    ## Guess we'll need to figure these out later?! Adapted from ES-CN:
    "ES-IB": 0,
    "ES-IB-FO": 0,
    "ES-IB-IZ": 0,
    "ES-IB-MA": 0,
    "ES-IB-ME": 0,
}


def fetch_island_data(zone_key: str, session):
    if zone_key == "ES-CN-FVLZ":
        lanzarote_fuerteventura_data = LanzaroteFuerteventura(session).get_all()
        if not lanzarote_fuerteventura_data:
            raise ParserException(zone_key, "LanzaroteFuerteventura not response")
        else:
            return lanzarote_fuerteventura_data
    elif zone_key == "ES-CN-GC":
        gran_canaria_data = GranCanaria(session).get_all()
        if not gran_canaria_data:
            raise ParserException(zone_key, "GranCanaria not response")
        else:
            return gran_canaria_data
    elif zone_key == "ES-CN-IG":
        gomera_data = Gomera(session).get_all()
        if not gomera_data:
            raise ParserException(zone_key, "Gomera doesn't response")
        else:
            return gomera_data
    elif zone_key == "ES-CN-LP":
        la_palma_data = LaPalma(session).get_all()
        if not la_palma_data:
            raise ParserException(zone_key, "LaPalma doesn't response")
        else:
            return la_palma_data
    elif zone_key == "ES-CN-TE":
        tenerife_data = Tenerife(session).get_all()
        if not tenerife_data:
            raise ParserException(zone_key, "Tenerife doesn't response")
        else:
            return tenerife_data
    elif zone_key == "ES-CN-HI":
        el_hierro_data = ElHierro(session).get_all()
        if not el_hierro_data:
            raise ParserException(zone_key, "ElHierro doesn't response")
        else:
            return el_hierro_data
    elif zone_key == "ES-IB-FO":
        formentera_data = Formentera(session).get_all()
        if not formentera_data:
            raise ParserException(zone_key, "Formentera doesn't respond")
        else:
            return formentera_data
    elif zone_key == "ES-IB-IZ":
        ibiza_data = Ibiza(session).get_all()
        if not ibiza_data:
            raise ParserException(zone_key, "Party is over, Ibiza doesn't respond")
        else:
            return ibiza_data
    elif zone_key == "ES-IB-MA":
        mallorca_data = Mallorca(session).get_all()
        if not mallorca_data:
            raise ParserException(zone_key, "Mallorca doesn't respond")
        else:
            return mallorca_data
    elif zone_key == "ES-IB-ME":
        menorca_data = Menorca(session).get_all()
        if not menorca_data:
            raise ParserException(zone_key, "Menorca doesn't respond")
        else:
            return menorca_data
    elif zone_key == "ES-IB":
        balearic_islands = BalearicIslands(session).get_all()
        if not balearic_islands:
            raise ParserException(zone_key, "Balearic Islands doesn't respond")
        else:
            return balearic_islands
    else:
        raise ParserException(
            "ES.py",
            "This parser cannot return data for zone key: {0}".format(zone_key),
            zone_key,
        )


def fetch_consumption(
    zone_key: str,
    session=None,
    target_datetime: datetime.datetime | None = None,
    logger: logging.Logger | None = None,
) -> list:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []
    if island_data:
        for response in island_data:
            response_data = {
                "zoneKey": zone_key,
                "datetime": get(response.timestamp).datetime,
                "consumption": response.demand,
                "source": "demanda.ree.es",
            }

            data.append(response_data)

        return data
    else:
        raise ParserException(
            "ES.py",
            "No consumption data returned for zone key: {0}".format(zone_key),
            zone_key,
        )


def fetch_production(
    zone_key: str,
    session=None,
    target_datetime: datetime.datetime | None = None,
    logger: logging.Logger | None = logging.getLogger(__name__),
) -> list | None:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []

    if zone_key == "ES-IB":
        expected_range = {"coal": (50, 600)}
    else:
        expected_range = None

    if island_data:
        for response in island_data:
            if response.production() >= 0:
                response_data = {
                    "zoneKey": zone_key,
                    "datetime": get(response.timestamp).datetime,
                    "production": {
                        "coal": response.carbon,
                        "gas": round((response.gas + response.combined), 2),
                        "solar": response.solar,
                        "oil": round((response.vapor + response.diesel), 2),
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
                # Zone overrides

                # NOTE the LNG terminals are not built yet, so power generated by "gas" or "combined" in ES-CN domain is actually using oil.
                # Recheck this every 6 months and move to gas key if there has been a change.
                # Last checked: 2022-06-27
                if zone_key.split("-")[1] == "CN":
                    response_data["production"]["gas"] = 0.0
                    response_data["production"]["oil"] = round(
                        (
                            response.vapor
                            + response.diesel
                            + response.gas
                            + response.combined
                        ),
                        2,
                    )

                # Hydro response is hydro storage
                if zone_key == "ES-CN-HI":
                    response_data["production"]["hydro"] = 0.0
                    response_data["storage"]["hydro"] = -response.hydraulic

                response_data = validate(
                    response_data,
                    logger,
                    floor=FLOORS[zone_key],
                    expected_range=expected_range,
                )

                if response_data:
                    # append if valid
                    data.append(response_data)
        return data

    else:
        raise ParserException(
            "ES.py", "No production data returned for {0}".format(zone_key), zone_key
        )


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session=None,
    target_datetime: datetime.datetime | None = None,
    logger: logging.Logger | None = None,
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
    # Canary Islands
    print("fetch_consumption(ES-CN-FVLZ)")
    print(fetch_consumption("ES-CN-FVLZ"))
    print("fetch_production(ES-CN-FVLZ)")
    print(fetch_production("ES-CN-FVLZ"))
    print("fetch_consumption(ES-CN-GC)")
    print(fetch_consumption("ES-CN-GC"))
    print("fetch_production(ES-CN-GC)")
    print(fetch_production("ES-CN-GC"))
    print("fetch_consumption(ES-CN-IG)")
    print(fetch_consumption("ES-CN-IG"))
    print("fetch_production(ES-CN-IG)")
    print(fetch_production("ES-CN-IG"))
    print("fetch_consumption(ES-CN-LP)")
    print(fetch_consumption("ES-CN-LP"))
    print("fetch_production(ES-CN-LP)")
    print(fetch_production("ES-CN-LP"))
    print("fetch_consumption(ES-CN-TE)")
    print(fetch_consumption("ES-CN-TE"))
    print("fetch_production(ES-CN-TE)")
    print(fetch_production("ES-CN-TE"))
    print("fetch_consumption(ES-CN-HI)")
    print(fetch_consumption("ES-CN-HI"))
    print("fetch_production(ES-CN-HI)")
    print(fetch_production("ES-CN-HI"))

    # Balearic Islands
    print("fetch_consumption(ES-IB)")
    print(fetch_consumption("ES-IB"))
    print("fetch_production(ES-IB)")
    print(fetch_production("ES-IB"))
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

    # Exchanges
    print("fetch_exchange(ES, ES-IB)")
    print(fetch_exchange("ES", "ES-IB"))
    print("fetch_exchange(ES, ES-IB-MA)")
    print(fetch_exchange("ES", "ES-IB-MA"))
    print("fetch_exchange(ES-IB-MA, ES-IB-ME)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-ME"))
    print("fetch_exchange(ES-IB-MA, ES-IB-IZ)")
    print(fetch_exchange("ES-IB-MA", "ES-IB-IZ"))
    print("fetch_exchange(ES-IB-IZ, ES-IB-FO)")
    print(fetch_exchange("ES-IB-IZ", "ES-IB-FO"))
