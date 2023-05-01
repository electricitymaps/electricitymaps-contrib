#!/usr/bin/env python3

import json
import math
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.utils import get_token
from parsers.lib.validation import (
    validate,
    validate_consumption,
    validate_production_diffs,
)

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
DATASET_REAL_TIME = "eco2mix-national-tr"
DATASET_CONSOLIDATED = "eco2mix-national-cons-def"  # API called is Données éCO2mix nationales consolidées et définitives for datetimes older than 9 months


DELTA_15 = timedelta(minutes=15)


def is_not_nan_and_truthy(v) -> bool:
    if isinstance(v, float) and math.isnan(v):
        return False
    return bool(v)


def get_dataset_from_datetime(target_datetime: datetime) -> str:
    """Returns the dataset to query based on the target_datetime. The real-time API returns no values for target datetimes older than 9 months and we need to query the consolidated dataset."""
    if target_datetime < arrow.now(tz="Europe/Paris").shift(months=-9):
        # API called is Données éCO2mix régionales consolidées et définitives for datetimes that are more than 9 months in the past
        dataset = DATASET_CONSOLIDATED
    else:
        dataset = DATASET_REAL_TIME
    return dataset


def get_data(
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
) -> pd.DataFrame:
    """Returns a DataFrame with the data from the API."""
    if target_datetime:
        target_datetime_in_arrow = arrow.get(target_datetime).replace(
            tzinfo="Europe/Paris"
        )
    else:
        target_datetime_in_arrow = arrow.now(tz="Europe/Paris")

    # get dataset to query
    dataset = get_dataset_from_datetime(target_datetime_in_arrow)

    # setup request
    r = session or Session()
    formatted_from = target_datetime_in_arrow.shift(days=-1).format("YYYY-MM-DDTHH:mm")
    formatted_to = target_datetime_in_arrow.format("YYYY-MM-DDTHH:mm")

    params = {
        "dataset": dataset,
        "q": f"date_heure >= {formatted_from} AND date_heure <= {formatted_to}",
        "timezone": "Europe/Paris",
        "rows": 100,
    }

    params["apikey"] = get_token("RESEAUX_ENERGIES_TOKEN")
    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    data = json.loads(response.content)
    data = [d["fields"] for d in data["records"]]
    df = pd.DataFrame(data)
    return df


def reindex_data(df_to_reindex: pd.DataFrame) -> pd.DataFrame:
    """Reindex data to get averaged half-hourly values instead of quart-hourly values. This is done to ensure consistency between the historical set (1/2 hourly granularity) and the real-time set (1/4 hourly granularity)"""
    df_to_reindex = df_to_reindex.copy()
    # Round dates to the lower bound with 30 minutes granularity
    df_to_reindex["datetime"] = df_to_reindex["date_heure"].apply(
        lambda x: arrow.get(x).datetime
    )
    df_to_reindex["datetime_30"] = df_to_reindex["datetime"].apply(
        lambda x: x if x.minute in [0, 30] else x - DELTA_15
    )

    # Average data points corresponding to the same time with 30 min granularity
    df_reindexed = df_to_reindex.groupby("datetime_30").mean().reset_index()
    df_reindexed = df_reindexed.rename(columns={"datetime_30": "date_heure"})
    return df_reindexed


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "FR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    df_production = get_data(session, target_datetime)

    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys()) + MAP_HYDRO
    missing_fuels = [v for v in value_columns if v not in df_production.columns]
    present_fuels = [v for v in value_columns if v in df_production.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning("No fuels present in the API response")
        return list()
    elif len(missing_fuels) > 0:
        mf_str = ", ".join(missing_fuels)
        logger.warning(
            "Fuels [{}] are not present in the API " "response".format(mf_str)
        )

    df_production = df_production.loc[:, ["date_heure"] + present_fuels]
    df_production[present_fuels] = df_production[present_fuels].astype(float)

    # reindex df_production to get 1/2 hourly values
    df_production_reindexed = reindex_data(df_production)
    df_production_reindexed = df_production_reindexed.dropna(how="any", axis=0)

    datapoints = list()
    for row in df_production_reindexed.iterrows():
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
            i in df_production_reindexed.columns
            for i in ["hydraulique_lacs", "hydraulique_fil_eau_eclusee"]
        )
        has_hydro_storage = all(
            i in df_production_reindexed.columns
            for i in ["pompage", "hydraulique_step_turbinage"]
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
            "datetime": arrow.get(row[1]["date_heure"])
            .replace(tzinfo="Europe/Paris")
            .datetime,
            "production": production,
            "storage": storage,
            "source": "opendata.reseaux-energies.fr",
        }
        datapoint = validate(datapoint, logger, required=["nuclear", "hydro", "gas"])
        datapoints.append(datapoint)

    max_diffs = {
        "hydro": 5200,
        "solar": 3500,
        "coal": 1200,
        "wind": 5000,
        "nuclear": 8000,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "FR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    df_consumption = get_data(session, target_datetime)
    df_consumption = df_consumption[["date_heure", "consommation"]].dropna()

    # reindex df_consumption to get 1/2 hourly values
    df_consumption_reindexed = reindex_data(df_consumption)
    datapoints = []
    for row in df_consumption_reindexed.itertuples():
        datapoints.append(
            {
                "zoneKey": zone_key,
                "datetime": arrow.get(row.date_heure)
                .replace(tzinfo="Europe/Paris")
                .datetime,
                "consumption": row.consommation,
                "source": "opendata.reseaux-energies.fr",
            }
        )
    validated_datapoints = [
        validate_consumption(datapoint, logger) for datapoint in datapoints
    ]
    return validated_datapoints


if __name__ == "__main__":
    print(fetch_consumption())
    print(fetch_production(target_datetime="2023-03-01"))
