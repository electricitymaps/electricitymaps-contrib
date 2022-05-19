#!/usr/bin/env python3

import json
import logging
import math
import os
import xml.etree.ElementTree as ET
from datetime import timedelta

import arrow
import pandas as pd
import requests

from parsers.lib.config import refetch_frequency

from .lib.utils import get_token
from .lib.validation import validate, validate_production_diffs

API_ENDPOINT = "https://opendata.reseaux-energies.fr/api/records/1.0/search/"

MAP_GENERATION = {
    "nucleaire": "nuclear",
    "charbon": "coal",
    "gaz": "gas",
    "fioul": "oil",
    "eolien": "wind",
    "solaire": "solar",
    "bioenergies": "biomass",
}

MAP_HYDRO = [
    "hydraulique_fil_eau_eclusee",
    "hydraulique_lacs",
    "hydraulique_step_turbinage",
    "pompage",
]


def is_not_nan_and_truthy(v) -> bool:
    if isinstance(v, float) and math.isnan(v):
        return False
    return bool(v)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="FR",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    if target_datetime:
        to = arrow.get(target_datetime, "Europe/Paris")
    else:
        to = arrow.now(tz="Europe/Paris")

    # setup request
    r = session or requests.session()
    formatted_from = to.shift(days=-1).format("YYYY-MM-DDTHH:mm")
    formatted_to = to.format("YYYY-MM-DDTHH:mm")

    params = {
        "dataset": "eco2mix-national-tr",
        "q": "date_heure >= {} AND date_heure <= {}".format(
            formatted_from, formatted_to
        ),
        "timezone": "Europe/Paris",
        "rows": 100,
    }

    params["apikey"] = get_token("RESEAUX_ENERGIES_TOKEN")

    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    data = json.loads(response.content)
    data = [d["fields"] for d in data["records"]]
    df = pd.DataFrame(data)

    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys()) + MAP_HYDRO
    missing_fuels = [v for v in value_columns if v not in df.columns]
    present_fuels = [v for v in value_columns if v in df.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning("No fuels present in the API response")
        return list()
    elif len(missing_fuels) > 0:
        mf_str = ", ".join(missing_fuels)
        logger.warning(
            "Fuels [{}] are not present in the API " "response".format(mf_str)
        )

    df = df.loc[:, ["date_heure"] + present_fuels]
    df[present_fuels] = df[present_fuels].astype(float)

    datapoints = list()
    for row in df.iterrows():
        production = dict()
        for key, value in MAP_GENERATION.items():
            if key not in present_fuels:
                continue

            if -50 < row[1][key] < 0:
                # set small negative values to 0
                logger.warning("Setting small value of %s (%s) to 0." % (key, value))
                production[value] = 0
            else:
                production[value] = row[1][key]

        # Hydro is a special case!
        has_hydro_production = all(
            i in df.columns for i in ["hydraulique_lacs", "hydraulique_fil_eau_eclusee"]
        )
        has_hydro_storage = all(
            i in df.columns for i in ["pompage", "hydraulique_step_turbinage"]
        )
        if has_hydro_production:
            production["hydro"] = (
                row[1]["hydraulique_lacs"] + row[1]["hydraulique_fil_eau_eclusee"]
            )
        if has_hydro_storage:
            storage = {
                "hydro": row[1]["pompage"] * -1
                + row[1]["hydraulique_step_turbinage"] * -1
            }
        else:
            storage = dict()

        # if all production values are null, ignore datapoint
        if not any([is_not_nan_and_truthy(v) for k, v in production.items()]):
            continue

        datapoint = {
            "zoneKey": zone_key,
            "datetime": arrow.get(row[1]["date_heure"]).datetime,
            "production": production,
            "storage": storage,
            "source": "opendata.reseaux-energies.fr",
        }
        datapoint = validate(datapoint, logger, required=["nuclear", "hydro", "gas"])
        datapoints.append(datapoint)

    max_diffs = {
        "hydro": 1600,
        "solar": 500,
        "coal": 500,
        "wind": 1000,
        "nuclear": 1300,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key, session=None, target_datetime=None, logger=logging.getLogger(__name__)
) -> list:
    if target_datetime:
        now = arrow.get(target_datetime, tz="Europe/Paris")
    else:
        now = arrow.now(tz="Europe/Paris")

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


if __name__ == "__main__":
    print(fetch_production())
