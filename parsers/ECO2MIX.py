#!/usr/bin/env python3

import json
import math
import os
from datetime import datetime, timedelta
from logging import Logger, getLogger

import arrow
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from electricitymap.contrib.config import ZONES_CONFIG
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

from .lib.validation import validate, validate_production_diffs

# From RTE domain to EM domain
MAP_ZONES = {
    "France": "FR",
    **{
        subzone.replace("FR-", ""): subzone
        for subzone in ZONES_CONFIG["FR"].get("subZoneNames", [])
    },
    "BE": "BE",
    "CH": "CH",
    "DE": "DE",
    "ES": "ES",
    "GB": "GB",
    "IT": "IT-NO",
    "LU": "LU",
}

MAP_MODES = {
    "NuclÃ©aire": "production.nuclear",
    "Thermique": "production.unknown",
    "Eolien": "production.wind",
    "Solaire": "production.solar",
    "Hydraulique": "production.hydro",
    "Bioénergies": "production.biomass",
    "Consommation": "consumption",
    "Autres": "production.unknown",
    "Charbon": "production.coal",
    "Fioul": "production.oil",
    "Gaz": "production.gas",
    "Pompage": "storage.hydro",
    "Destockage": "storage.hydro",
    "Batterie_Injection": "storage.battery",
    "Batterie_Soutirage": "storage.battery",
    "Stockage": "storage.battery",
    "Solde": "IGNORED",
    "Co2": "IGNORED",
    "Taux de Co2": "IGNORED",
    "PrÃ©visionJ": "IGNORED",
    "PrÃ©visionJ-1": "IGNORED",
}

# validations for each region
VALIDATIONS = {
    "FR-ARA": ["unknown", "nuclear", "hydro"],
}


def query(url_type_arg, session=None, target_datetime=None):
    if target_datetime:
        date_to = arrow.get(target_datetime, "Europe/Paris")
    else:
        date_to = arrow.now(tz="Europe/Paris")
    date_from = date_to.shift(days=-1).floor("day")

    url = f"http://www.rte-france.com/getEco2MixXml.php?type={url_type_arg}&dateDeb={date_from.format('DD/MM/YYYY')}&dateFin={date_to.format('DD/MM/YYYY')}"
    if url_type_arg == "regionFlux":
        url = url.replace("dateDeb", "dateDebut")
    r = session or requests.session()
    response = r.get(url, verify=False)
    response.raise_for_status()
    return response.text


def query_exchange(session=None, target_datetime=None):
    return query(
        url_type_arg="regionFlux", session=session, target_datetime=target_datetime
    )


def query_production(session=None, target_datetime=None):
    return query(
        url_type_arg="region", session=session, target_datetime=target_datetime
    )


def parse_production_to_df(text):
    bs_content = BeautifulSoup(text, features="xml")
    # Flatten
    df = pd.DataFrame(
        [
            {
                **valeur.attrs,
                **valeur.parent.attrs,
                **valeur.parent.parent.attrs,
                "value": valeur.contents[0],
            }
            for valeur in bs_content.find_all("valeur")
        ]
    )
    if df.empty:
        return df
    # Add datetime
    df["datetime"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
        df["periode"].astype("int") * 15, unit="minute"
    )
    df.datetime = df.datetime.dt.tz_localize("Europe/Paris")
    # Set index
    df = df.set_index("datetime").drop(["date", "periode"], axis=1)
    # Remove invalid granularities
    df = df[df.granularite == "Global"].drop("granularite", axis=1)
    # Create key (will crash if a mode is not in the map and ensures we coded this right)
    df["key"] = df.v.apply(lambda k: MAP_MODES[k])
    # Filter out invalid modes
    df = df[df.key != "IGNORED"]
    # Compute zone_key
    df["zone_key"] = df["perimetre"].apply(lambda k: MAP_ZONES[k])
    # Compute values
    df.value = df.value.replace("ND", np.nan).replace("-", np.nan).astype("float")
    # Storage works the other way around (RTE treats storage as production)
    df.loc[df.key.str.startswith("storage."), "value"] *= -1
    return df


def format_production_df(df, zone_key):
    if df.empty:
        return []
    # There can be multiple rows with the same key
    # (e.g. multiple things lumping into `unknown`)
    # so we need to group them and sum.
    df = (
        df[df.zone_key == zone_key]
        .reset_index()
        .groupby(["datetime", "key"])
        # We use `min_count=1` to make sure at least one non-NaN
        # value is present to compute a sum.
        .sum(min_count=1)
        # We unstack `key` which creates a df where keys are columns
        .unstack("key")["value"]
    )
    return [
        {
            "zoneKey": zone_key,
            "datetime": ts.to_pydatetime(),
            "production": (
                row.filter(like="production.")
                .rename(lambda c: c.replace("production.", ""))
                .to_dict()
            ),
            "storage": (
                row.filter(like="storage.")
                .rename(lambda c: c.replace("storage.", ""))
                .to_dict()
            ),
            "source": "rte-france.com/eco2mix",
        }
        for (ts, row) in df.iterrows()
    ]


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key, session=None, target_datetime=None, logger: Logger = getLogger(__name__)
):
    if zone_key == "FR-COR":
        raise ParserException("FR-COR is not supported in this parser")

    datapoints = [
        validate(d, logger, required=VALIDATIONS.get(zone_key, []))
        for d in format_production_df(
            df=parse_production_to_df(query_production(session, target_datetime)),
            zone_key=zone_key,
        )
    ]

    max_diffs = {
        # "hydro": 1600,
        # "solar": 500,
        # "unknown": 2000,  # thermal
        # "wind": 1000,
        # "nuclear": 1300,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints


def parse_exchange_to_df(text):
    bs_content = BeautifulSoup(text, features="xml")
    # Flatten
    df = pd.DataFrame(
        [
            {
                **valeur.attrs,
                **valeur.parent.attrs,
                **valeur.parent.parent.attrs,
                "value": valeur.contents[0],
            }
            for valeur in bs_content.find_all("valeur")
        ]
    )
    # Add datetime
    if df.empty:
        return df
    df["datetime"] = pd.to_datetime(df["date"]) + pd.to_timedelta(
        df["periode"].astype("int") * 15, unit="minute"
    )
    df.datetime = df.datetime.dt.tz_localize("Europe/Paris")
    # Set index
    df = df.set_index("datetime").drop(["date", "periode"], axis=1)
    # Remove invalid granularities
    df = df[df.granularite == "Global"].drop("granularite", axis=1)
    # Compute values
    df.value = df.value.replace("ND", np.nan).replace("-", np.nan).astype("float")
    df["zone_key_other"] = df.v.apply(lambda x: MAP_ZONES[x.split("_")[1]])
    df["zone_key"] = df.perimetre.apply(lambda k: MAP_ZONES[k])
    df["sorted_zone_keys"] = df.apply(
        lambda row: "->".join(sorted([row["zone_key"], row["zone_key_other"]])), axis=1
    )
    # Data comes in for all zones, which means on zone's import
    # will be another's export. We therefore only keep one of them
    df = df[
        df.perimetre
        == df.sorted_zone_keys.apply(
            # make sure we only selected rows where `perimetre`
            # is one of the FR- keys of the pair (to make sure we capture
            # exchange with neighboring countries)
            lambda k: [
                zone_key.replace("FR-", "")
                for zone_key in k.split("->")
                if "FR-" in zone_key
            ][0]
        )
    ]
    # RTE defines flow in the follow way:
    # `value` represents flow from `zone_key_other` to `zone_key` (`perimetre`)
    # We here flip the sign if the alphabetical order requires it
    # (e.g. if zone_key is not the second key)
    df["net_flow"] = df.apply(
        lambda row: row["value"]
        if row["sorted_zone_keys"].split("->")[1] == row["zone_key"]
        else row["value"] * -1,
        axis=1,
    )
    return df


def format_exchange_df(df, sorted_zone_keys):
    # There can be multiple rows with the same key
    # (e.g. multiple things lumping into `unknown`)
    # so we need to group them and sum.
    if df.empty:
        return []
    df = (
        df[df.sorted_zone_keys == sorted_zone_keys]
        .reset_index()
        .groupby(["datetime"])
        # We use `min_count=1` to make sure at least one non-NaN
        # value is present to compute a sum.
        .sum(min_count=1)
    )
    return [
        {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": ts.to_pydatetime(),
            "netFlow": row.net_flow,
            "source": "rte-france.com/eco2mix",
        }
        for (ts, row) in df.iterrows()
    ]


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger: Logger = getLogger(__name__),
):

    datapoints = format_exchange_df(
        df=parse_exchange_to_df(query_exchange(session, target_datetime)),
        sorted_zone_keys="->".join(sorted([zone_key1, zone_key2])),
    )
    return datapoints
