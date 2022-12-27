#!/usr/bin/env python3
# coding=utf-8


from datetime import datetime, time
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
from requests import Session

TIMEZONE = "America/Costa_Rica"
# POWER_PLANTS = {
#     "Aeroenergía": "wind",
#     "Altamira": "wind",
#     "Angostura": "hydro",
#     "Arenal": "hydro",
#     "Balsa Inferior": "hydro",
#     "Barranca": "oil",
#     "Barro Morado": "geothermal",
#     "Belén": "hydro",
#     "Bijagua": "hydro",
#     "Birris12": "hydro",
#     "Birris3": "hydro",
#     "Boca de Pozo": "hydro",
#     "CNFL": "hydro",
#     "Cachí": "hydro",
#     "Campos Azules": "wind",
#     "Canalete": "hydro",
#     "Cariblanco": "hydro",
#     "Carrillos": "hydro",
#     "Caño Grande": "hydro",
#     "Caño Grande III": "hydro",
#     "Chiripa": "wind",
#     "Chocosuelas": "hydro",
#     "Chucás": "hydro",
#     "Cote": "hydro",
#     "Cubujuquí": "hydro",
#     "Daniel Gutiérrez": "hydro",
#     "Dengo": "hydro",
#     "Don Pedro": "hydro",
#     "Doña Julia": "hydro",
#     "Echandi": "hydro",
#     "Electriona": "hydro",
#     "El Encanto": "hydro",
#     "El Angel": "hydro",
#     "El Angel Ampliación": "hydro",
#     "El Embalse": "hydro",
#     "El General": "hydro",
#     "El Viejo": "biomass",
#     "Garabito": "oil",
#     "Garita": "hydro",
#     "Guápiles": "oil",
#     "Hidrozarcas": "hydro",
#     "Jorge Manuel Dengo": "hydro",
#     "La Esperanza (CoopeL)": "hydro",
#     "La Joya": "hydro",
#     "Las Pailas II": "geothermal",
#     "Los Negros": "hydro",
#     "Los Negros II": "hydro",
#     "Los Santos": "wind",
#     "MOVASA": "wind",
#     "Matamoros": "hydro",
#     "Miravalles I": "geothermal",
#     "Miravalles II": "geothermal",
#     "Miravalles III": "geothermal",
#     "Miravalles V": "geothermal",
#     "Moín I": "oil",
#     "Moín II": "oil",
#     "Moín III": "oil",
#     "Orosí": "wind",
#     "Orotina": "oil",
#     "Otros": "hydra",
#     "PE Cacao": "wind",
#     "PE Mogote": "wind",
#     "PE Río Naranjo": "hydro",
#     "PEG": "wind",
#     "Pailas": "geothermal",
#     "Parque Solar Juanilama": "solar",
#     "Parque Solar Miravalles": "solar",
#     "Peñas Blancas": "hydro",
#     "Pirrís": "hydro",
#     "Plantas Eólicas": "wind",
#     "Platanar": "hydro",
#     "Pocosol": "hydro",
#     "Poás I y II": "hydro",
#     "Reventazón": "hydro",
#     "Río Lajas": "hydro",
#     "Río Macho": "hydro",
#     "Río Segundo": "hydro",
#     "San Antonio": "oil",
#     "San Lorenzo (C)": "hydro",
#     "Sandillal": "hydro",
#     "Suerkata": "hydro",
#     "Taboga": "biomass",
#     "Tacares": "hydro",
#     "Tejona": "wind",
#     "Tilawind": "wind",
#     "Torito": "hydro",
#     "Toro I": "hydro",
#     "Toro II": "hydro",
#     "Toro III": "hydro",
#     "Tuis (JASEC)": "hydro",
#     "Valle Central": "wind",
#     "Vara Blanca": "hydro",
#     "Ventanas": "hydro",
#     "Ventanas-Garita": "hydro",
#     "Vientos de La Perla": "wind",
#     "Vientos de Miramar": "wind",
#     "Vientos del Este": "wind",
#     "Volcán": "hydro",
# }

# Note: Ignoring Intercambio deliberately
SPANISH_TO_ENGLISH = {
    "Bagazo": "biomass",
    "Eólica": "wind",
    "Geotérmica": "geothermal",
    "Hidroeléctrica": "hydro",
    "Solar": "solar",
    "Térmica": "oil",
}

def empty_record(zone_key: str):
    return {
        "zoneKey": zone_key,
        "capacity": {},
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "nuclear": 0.0,
            "oil": 0.0,
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "unknown": 0.0,
        },
        "storage": {},
        "source": "grupoice.com",
    }

def fetch_production(
    zone_key: str = "CR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    # ensure we have an arrow object.
    # if no target_datetime is specified, this defaults to now.
    target_datetime = arrow.get(target_datetime).to(TIMEZONE)

    # if before 01:30am on the current day then fetch previous day due to
    # data lag.
    today = arrow.get().to(TIMEZONE).date()
    if target_datetime.date() == today:
        target_datetime = (
            target_datetime
            if target_datetime.time() >= time(1, 30)
            else target_datetime.shift(days=-1)
        )

    if target_datetime < arrow.get("2012-07-01"):
        # data availability limit found by manual trial and error
        logger.error(
            "CR API does not provide data before 2012-07-01, "
            "{} was requested".format(target_datetime),
            extra={"key": zone_key},
        )
        return None

    # Do not use existing session as some amount of cache is taking place
    r = Session()
    day = target_datetime.format("DD")
    month = target_datetime.format("MM")
    year = target_datetime.format("YYYY")
    url = f"https://apps.grupoice.com/CenceWeb/data/sen/json/EnergiaHorariaFuentePlanta?anno={year}&mes={month}&dia={day}"

    response = r.get(url)
    resp_data = response.json()["data"]

    results = {}
    for hourly_item in resp_data:
        if hourly_item["fuente"] == "Intercambio":
            continue
        if hourly_item["fecha"] not in results:
            results[hourly_item["fecha"]] = empty_record(zone_key)

        results[hourly_item["fecha"]]["datetime"] = arrow.get(hourly_item["fecha"], tzinfo=TIMEZONE).datetime
        results[hourly_item["fecha"]]["production"][SPANISH_TO_ENGLISH[hourly_item["fuente"]]] += hourly_item["dato"]
    
    return [results[k] for k in sorted(results.keys())]


# TODO: Source not available anymore. Need to find a new source for this.
# --------------------------------------------------------------------------------
# def fetch_exchange(
#     zone_key1: str = "CR",
#     zone_key2: str = "NI",
#     session: Optional[Session] = None,
#     target_datetime: Optional[datetime] = None,
#     logger: Logger = getLogger(__name__),
# ) -> dict:
#     """Requests the last known power exchange (in MW) between two regions."""
#     if target_datetime:
#         raise NotImplementedError("This parser is not yet able to parse past dates")

#     sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

#     df = pd.read_csv(
#         "http://www.enteoperador.org/newsite/flash/data.csv", index_col=False
#     )

#     if sorted_zone_keys == "CR->NI":
#         flow = df["NICR"][0]
#     elif sorted_zone_keys == "CR->PA":
#         flow = -1 * df["CRPA"][0]
#     else:
#         raise NotImplementedError("This exchange pair is not implemented")

#     data = {
#         "datetime": arrow.now(TIMEZONE).datetime,
#         "sortedZoneKeys": sorted_zone_keys,
#         "netFlow": flow,
#         "source": "enteoperador.org",
#     }

#     return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())

    # print('fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z")))

    # # this should work
    # print('fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z")))

    # # this should return None
    # print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    # pprint(fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z")))

    # print("fetch_exchange() ->")
    # print(fetch_exchange())
