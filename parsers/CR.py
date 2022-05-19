#!/usr/bin/env python3
# coding=utf-8

import datetime as dt
import logging

import arrow
import pandas as pd
import requests
from bs4 import BeautifulSoup

TIMEZONE = "America/Costa_Rica"
DATE_FORMAT = "DD/MM/YYYY"
MONTH_FORMAT = "MM/YYYY"
POWER_PLANTS = {
    "Aeroenergía": "wind",
    "Altamira": "wind",
    "Angostura": "hydro",
    "Arenal": "hydro",
    "Balsa Inferior": "hydro",
    "Barranca": "oil",
    "Barro Morado": "geothermal",
    "Belén": "hydro",
    "Bijagua": "hydro",
    "Birris12": "hydro",
    "Birris3": "hydro",
    "Boca de Pozo": "hydro",
    "CNFL": "hydro",
    "Cachí": "hydro",
    "Campos Azules": "wind",
    "Canalete": "hydro",
    "Cariblanco": "hydro",
    "Carrillos": "hydro",
    "Caño Grande": "hydro",
    "Caño Grande III": "hydro",
    "Chiripa": "wind",
    "Chocosuelas": "hydro",
    "Chucás": "hydro",
    "Cote": "hydro",
    "Cubujuquí": "hydro",
    "Daniel Gutiérrez": "hydro",
    "Dengo": "hydro",
    "Don Pedro": "hydro",
    "Doña Julia": "hydro",
    "Echandi": "hydro",
    "Electriona": "hydro",
    "El Encanto": "hydro",
    "El Angel": "hydro",
    "El Angel Ampliación": "hydro",
    "El Embalse": "hydro",
    "El General": "hydro",
    "El Viejo": "biomass",
    "Garabito": "oil",
    "Garita": "hydro",
    "Guápiles": "oil",
    "Hidrozarcas": "hydro",
    "Jorge Manuel Dengo": "hydro",
    "La Esperanza (CoopeL)": "hydro",
    "La Joya": "hydro",
    "Las Pailas II": "geothermal",
    "Los Negros": "hydro",
    "Los Negros II": "hydro",
    "Los Santos": "wind",
    "MOVASA": "wind",
    "Matamoros": "hydro",
    "Miravalles I": "geothermal",
    "Miravalles II": "geothermal",
    "Miravalles III": "geothermal",
    "Miravalles V": "geothermal",
    "Moín I": "oil",
    "Moín II": "oil",
    "Moín III": "oil",
    "Orosí": "wind",
    "Orotina": "unknown",
    "Otros": "unknown",
    "PE Cacao": "wind",
    "PE Mogote": "wind",
    "PE Río Naranjo": "hydro",
    "PEG": "wind",
    "Pailas": "geothermal",
    "Parque Solar Juanilama": "solar",
    "Parque Solar Miravalles": "solar",
    "Peñas Blancas": "hydro",
    "Pirrís": "hydro",
    "Plantas Eólicas": "wind",
    "Platanar": "hydro",
    "Pocosol": "hydro",
    "Poás I y II": "hydro",
    "Reventazón": "hydro",
    "Río Lajas": "hydro",
    "Río Macho": "hydro",
    "Río Segundo": "hydro",
    "San Antonio": "oil",
    "San Lorenzo (C)": "hydro",
    "Sandillal": "hydro",
    "Suerkata": "hydro",
    "Taboga": "biomass",
    "Tacares": "hydro",
    "Tejona": "wind",
    "Tilawind": "wind",
    "Torito": "hydro",
    "Toro I": "hydro",
    "Toro II": "hydro",
    "Toro III": "hydro",
    "Tuis (JASEC)": "hydro",
    "Valle Central": "wind",
    "Vara Blanca": "hydro",
    "Ventanas": "hydro",
    "Ventanas-Garita": "hydro",
    "Vientos de La Perla": "wind",
    "Vientos de Miramar": "wind",
    "Vientos del Este": "wind",
    "Volcán": "hydro",
}

CHARACTERISTIC_NAME = "Angostura"


def empty_record(zone_key):
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


def df_to_data(zone_key, day, df, logger):
    df = df.dropna(axis=1, how="any")
    # Check for empty dataframe
    if df.shape == (1, 1):
        return []
    df = df.drop(["Intercambio Sur", "Intercambio Norte", "Total"], errors="ignore")
    df = df.iloc[:, :-1]

    results = []
    unknown_plants = set()
    hour = 0
    for column in df:
        data = empty_record(zone_key)
        data_time = day.replace(hour=hour, minute=0, second=0, microsecond=0).datetime
        for index, value in df[column].items():
            source = POWER_PLANTS.get(index)
            if not source:
                source = "unknown"
                unknown_plants.add(index)
            data["datetime"] = data_time
            data["production"][source] += max(0.0, value)
        hour += 1
        results.append(data)

    for plant in unknown_plants:
        logger.warning(
            "{} is not mapped to generation type".format(plant), extra={"key": zone_key}
        )

    return results


def fetch_production(
    zone_key="CR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
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
            if target_datetime.time() >= dt.time(1, 30)
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
    r = requests.session()
    url = "https://apps.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf"
    response = r.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    jsf_view_state = soup.find("input", {"name": "javax.faces.ViewState"})["value"]

    data = [
        ("formPosdespacho:txtFechaInicio_input", target_datetime.format(DATE_FORMAT)),
        ("formPosdespacho:pickFecha", ""),
        ("formPosdespacho_SUBMIT", 1),
        ("javax.faces.ViewState", jsf_view_state),
    ]
    response = r.post(url, data=data)

    # tell pandas which table to use by providing CHARACTERISTIC_NAME
    df = pd.read_html(
        response.text, match=CHARACTERISTIC_NAME, skiprows=1, index_col=0
    )[0]

    results = df_to_data(zone_key, target_datetime, df, logger)

    return results


def fetch_exchange(
    zone_key1="CR", zone_key2="NI", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    df = pd.read_csv(
        "http://www.enteoperador.org/newsite/flash/data.csv", index_col=False
    )

    if sorted_zone_keys == "CR->NI":
        flow = df["NICR"][0]
    elif sorted_zone_keys == "CR->PA":
        flow = -1 * df["CRPA"][0]
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    data = {
        "datetime": arrow.now(TIMEZONE).datetime,
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": flow,
        "source": "enteoperador.org",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())

    print('fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z")))

    # this should work
    print('fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z")))

    # this should return None
    print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z")))

    print("fetch_exchange() ->")
    print(fetch_exchange())
