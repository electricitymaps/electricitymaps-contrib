#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZONES_CONFIG
from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

# from .lib.validation import validate, validate_production_diffs

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

SOURCE = "rte-france.com"


def query(url_type_arg, session: Session, target_datetime: datetime | None):
    if target_datetime:
        date_to = target_datetime.replace(tzinfo=ZoneInfo("Europe/Paris"))
    else:
        date_to = datetime.now(tz=ZoneInfo("Europe/Paris"))
    date_from = (date_to - timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    date_from = date_from.strftime("%d/%m/%Y")
    date_to = date_to.strftime("%d/%m/%Y")

    url = f"http://www.rte-france.com/getEco2MixXml.php?type={url_type_arg}&dateDeb={date_from}&dateFin={date_to}"
    if url_type_arg == "regionFlux":
        url = url.replace("dateDeb", "dateDebut")
    r = session or requests.session()
    response = r.get(url, verify=False)
    response.raise_for_status()
    return response.text


def query_exchange(session: Session, target_datetime: datetime | None):
    return query(
        url_type_arg="regionFlux", session=session, target_datetime=target_datetime
    )


def query_production(session: Session, target_datetime: datetime | None):
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
            "source": SOURCE,
        }
        for (ts, row) in df.iterrows()
    ]


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key, session=None, target_datetime=None, logger: Logger = getLogger(__name__)
):
    if zone_key == "FR-COR":
        raise ParserException("ECO2MIX.py", "FR-COR is not supported in this parser")

    datapoints = [
        # validate(d, logger, required=VALIDATIONS.get(zone_key, []))
        # for d in
        format_production_df(
            df=parse_production_to_df(query_production(session, target_datetime)),
            zone_key=zone_key,
        )
    ]

    # max_diffs = {
    #     # "hydro": 1600,
    #     # "solar": 500,
    #     # "unknown": 2000,  # thermal
    #     # "wind": 1000,
    #     # "nuclear": 1300,
    # }

    # datapoints = validate_production_diffs(datapoints, max_diffs, logger)

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


def format_exchange_df(df, sorted_zone_keys: ZoneKey, logger: Logger):
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
    exchange_list = ExchangeList(logger)
    for ts, row in df.iterrows():
        exchange_list.append(
            zoneKey=sorted_zone_keys,
            datetime=ts.to_pydatetime(),
            netFlow=row.net_flow,
            source=SOURCE,
        )
    return exchange_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    session = session or Session()
    datapoints = format_exchange_df(
        df=parse_exchange_to_df(query_exchange(session, target_datetime)),
        sorted_zone_keys=ZoneKey("->".join(sorted([zone_key1, zone_key2]))),
        logger=logger,
    )
    return datapoints


if __name__ == "__main__":
    session = requests.Session()
    # target_datetime = datetime.now(tz=ZoneInfo("Europe/Paris"))
    target_datetime = datetime(2025, 8, 19, 0, 0, 0, tzinfo=ZoneInfo("Europe/Paris"))
    print(
        fetch_production(
            zone_key="FR-ARA", session=session, target_datetime=target_datetime
        )
    )
    print(
        fetch_exchange(
            zone_key1=ZoneKey("FR-BRE"),
            zone_key2=ZoneKey("FR-PLO"),
            session=session,
            target_datetime=target_datetime,
        )
    )
    print(
        fetch_exchange(
            zone_key1=ZoneKey("FR-BRE"),
            zone_key2=ZoneKey("FR-NOR"),
            session=session,
            target_datetime=target_datetime,
        )
    )
