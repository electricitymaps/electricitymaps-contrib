#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.utils import get_token

API_ENDPOINT = "https://opendata.reseaux-energies.fr/api/records/1.0/search/"

MAP_GENERATION = {
    "nucleaire": "nuclear",
    "charbon": "coal",
    "gaz": "gas",
    "fioul": "oil",
    "eolien": "wind",
    "solaire": "solar",
    "bioenergies": "biomass",
    "hydraulique_fil_eau_eclusee": "hydro",
    "hydraulique_lacs": "hydro",
    "hydraulique_step_turbinage": "hydro_storage",
    "pompage": "hydro_storage",
    "stockage_batterie": "battery_storage",
    "destockage_batterie": "battery_storage",
}

STORAGE_MODES = ["hydro_storage", "battery_storage"]
DATASET_REAL_TIME = "eco2mix-national-tr"
DATASET_CONSOLIDATED = "eco2mix-national-cons-def"  # API called is Données éCO2mix nationales consolidées et définitives for datetimes older than 9 months


DELTA_15 = timedelta(minutes=15)
TZ = ZoneInfo("Europe/Paris")
SOURCE = "opendata.reseaux-energies.fr"


def get_dataset_from_datetime(target_datetime: datetime) -> str:
    """Returns the dataset to query based on the target_datetime. The real-time API returns no values for target datetimes older than 9 months and we need to query the consolidated dataset."""
    if target_datetime < datetime(2022, 5, 31, tzinfo=TZ):
        # API called is Données éCO2mix régionales consolidées et définitives for datetimes before May 2022
        dataset = DATASET_CONSOLIDATED
    else:
        dataset = DATASET_REAL_TIME
    return dataset


def get_data(
    session: Session | None = None,
    target_datetime: datetime | None = None,
) -> pd.DataFrame:
    """Returns a DataFrame with the data from the API."""
    if target_datetime:
        target_datetime_localised = target_datetime.replace(tzinfo=TZ)
    else:
        target_datetime_localised = datetime.now(tz=TZ)

    # get dataset to query
    dataset = get_dataset_from_datetime(target_datetime_localised)

    # setup request
    r = session or Session()
    formatted_from = (target_datetime_localised - timedelta(days=1)).strftime(
        "%Y-%m-%dT%H:%M"
    )
    formatted_to = target_datetime_localised.strftime("%Y-%m-%dT%H:%M")

    params = {
        "dataset": dataset,
        "q": f"date_heure >= {formatted_from} AND date_heure <= {formatted_to}",
        "timezone": "Europe/Paris",
        "rows": 100,
    }

    params["apikey"] = get_token("RESEAUX_ENERGIES_TOKEN")
    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    if not response.ok:
        raise ValueError(
            f"Failed to fetch data from {API_ENDPOINT}. Status code: {response.status_code}"
        )
    data = response.json()
    data = [d["fields"] for d in data["records"]]
    df = pd.DataFrame(data)
    return df


def reindex_data(df_to_reindex: pd.DataFrame) -> pd.DataFrame:
    """Reindex data to get averaged half-hourly values instead of quart-hourly values. This is done to ensure consistency between the historical set (1/2 hourly granularity) and the real-time set (1/4 hourly granularity)"""
    df_to_reindex = df_to_reindex.copy()
    # Round dates to the lower bound with 30 minutes granularity
    df_to_reindex["datetime"] = pd.to_datetime(
        df_to_reindex["date_heure"]
    ).dt.tz_convert(TZ)
    df_to_reindex["datetime_30"] = df_to_reindex["datetime"].apply(
        lambda x: x if x.minute in [0, 30] else x - DELTA_15
    )

    # Average data points corresponding to the same time with 30 min granularity
    df_reindexed = (
        df_to_reindex.groupby("datetime_30").mean(numeric_only=True).reset_index()
    )
    df_reindexed = df_reindexed.rename(columns={"datetime_30": "date_heure"})
    return df_reindexed.set_index("date_heure")


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("FR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    df_production = get_data(session, target_datetime)
    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys())
    missing_fuels = [v for v in value_columns if v not in df_production.columns]
    present_fuels = [v for v in value_columns if v in df_production.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning("No fuels present in the API response")
        return []
    elif len(missing_fuels) > 0:
        mf_str = ", ".join(missing_fuels)
        logger.warning(f"Fuels [{mf_str}] are not present in the API " "response")

    df_production = df_production.loc[:, ["date_heure"] + present_fuels]
    df_production[present_fuels] = df_production[present_fuels].astype(float)

    # reindex df_production to get 1/2 hourly values
    df_production_reindexed = reindex_data(df_production)
    df_production_reindexed = df_production_reindexed.dropna(how="any", axis=0)
    df_production_reindexed = df_production_reindexed.rename(columns=MAP_GENERATION)
    df_production_reindexed = df_production_reindexed.groupby(
        df_production_reindexed.columns, axis=1
    ).sum()

    production_mixes = ProductionBreakdownList(logger)
    for idx, row in df_production_reindexed.iterrows():
        productionMix = ProductionMix()
        storageMix = StorageMix()
        for mode in row.index:
            if mode in STORAGE_MODES:
                storageMix.add_value(mode.split("_")[0], -1 * row[mode])
            else:
                productionMix.add_value(mode, row[mode])
        production_mixes.append(
            zoneKey=zone_key,
            production=productionMix,
            storage=storageMix,
            datetime=idx.to_pydatetime(),
            source=SOURCE,
        )
    return production_mixes.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("FR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    df_consumption = get_data(session, target_datetime)
    df_consumption = df_consumption[["date_heure", "consommation"]].dropna()

    # reindex df_consumption to get 1/2 hourly values
    df_consumption_reindexed = reindex_data(df_consumption)
    consumption_list = TotalConsumptionList(logger)
    for row in df_consumption_reindexed.itertuples():
        consumption_list.append(
            zoneKey=zone_key,
            consumption=row.consommation,
            datetime=row.Index.to_pydatetime(),
            source=SOURCE,
        )

    return consumption_list.to_list()
