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
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.utils import get_token
from electricitymap.contrib.types import ZoneKey

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
DATASET_REAL_TIME = "eco2mix-national-tr"  # API called is Données éCO2mix nationales en temps réel if no consolidated data is available
DATASET_CONSOLIDATED = "eco2mix-national-cons-def"  # API called is Données éCO2mix nationales consolidées et définitives


DELTA_15 = timedelta(minutes=15)
TZ = ZoneInfo("Europe/Paris")
SOURCE = "opendata.reseaux-energies.fr"

# Fetch one extra quarter-hour on each side of the requested window so the 30-min
# reindex buckets at the window edges always contain both of their quarter-hour
# points. Without this a boundary bucket gets averaged from a single point on
# some refetches and from two points on others, making the stored value flip
# back and forth (data churn). The padding is trimmed off after reindexing.
WINDOW_PADDING = DELTA_15
# 24h + padding at 1/4h granularity is ~98 points; keep headroom so the response
# is never truncated (a truncated edge would itself cause churn).
API_ROWS = 200


def _window_bounds(target_datetime: datetime | None) -> tuple[datetime, datetime]:
    """Return the requested window (start, end) in Europe/Paris time.

    ``target_datetime`` is *converted* to Europe/Paris (not relabelled), so a
    UTC-aware datetime from the pipeline maps to the correct local window.
    """
    end = (
        datetime.now(tz=TZ)
        if target_datetime is None
        else target_datetime.astimezone(TZ)
    )
    return end - timedelta(days=1), end


def get_data(
    dt_from: datetime, dt_to: datetime, session: Session | None = None
) -> pd.DataFrame:
    """Returns data from the consolidated data endpoint if it is available, otherwise returns data from the real-time data endpoint."""
    df_consolidated = request_data(DATASET_CONSOLIDATED, dt_from, dt_to, session)
    if df_consolidated.empty:
        return request_data(DATASET_REAL_TIME, dt_from, dt_to, session)
    return df_consolidated


def request_data(
    dataset: str,
    dt_from: datetime,
    dt_to: datetime,
    session: Session | None = None,
) -> pd.DataFrame:
    """Returns a DataFrame with the data from the API for the [dt_from, dt_to] window."""
    r = session or Session()
    params = {
        "dataset": dataset,
        "q": (
            f"date_heure >= {dt_from.strftime('%Y-%m-%dT%H:%M')} "
            f"AND date_heure <= {dt_to.strftime('%Y-%m-%dT%H:%M')}"
        ),
        "timezone": "Europe/Paris",
        "rows": API_ROWS,
        "apikey": get_token("RESEAUX_ENERGIES_TOKEN"),
    }
    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    if not response.ok:
        raise ValueError(
            f"Failed to fetch data from {API_ENDPOINT}. Status code: {response.status_code}"
        )
    data = response.json()
    data = [d["fields"] for d in data["records"]]
    return pd.DataFrame(data)


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
    window_start, window_end = _window_bounds(target_datetime)
    df_production = get_data(
        window_start - WINDOW_PADDING, window_end + WINDOW_PADDING, session
    )
    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys())
    missing_fuels = [v for v in value_columns if v not in df_production.columns]
    present_fuels = [v for v in value_columns if v in df_production.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning("No fuels present in the API response")
        return []
    elif len(missing_fuels) > 0:
        mf_str = ", ".join(missing_fuels)
        logger.warning(f"Fuels [{mf_str}] are not present in the API response")

    df_production = df_production.loc[:, ["date_heure"] + present_fuels]
    df_production[present_fuels] = df_production[present_fuels].astype(float)

    # reindex df_production to get 1/2 hourly values
    df_production_reindexed = reindex_data(df_production)
    df_production_reindexed = df_production_reindexed.dropna(how="any", axis=0)
    # Trim the padding: keep only buckets inside the originally requested window.
    # The padding above guaranteed these boundary buckets were averaged from both
    # of their quarter-hour points, so the value no longer depends on where the
    # fetch window edge happened to fall.
    df_production_reindexed = df_production_reindexed[
        (df_production_reindexed.index >= window_start)
        & (df_production_reindexed.index <= window_end)
    ]
    df_production_reindexed = df_production_reindexed.rename(columns=MAP_GENERATION)
    df_production_reindexed = df_production_reindexed.groupby(
        df_production_reindexed.columns, axis=1
    ).sum(
        numeric_only=True,
    )

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
    window_start, window_end = _window_bounds(target_datetime)
    df_consumption = get_data(
        window_start - WINDOW_PADDING, window_end + WINDOW_PADDING, session
    )
    df_consumption = df_consumption[["date_heure", "consommation"]].dropna()

    # reindex df_consumption to get 1/2 hourly values
    df_consumption_reindexed = reindex_data(df_consumption)
    # Trim the padding back to the originally requested window (see fetch_production).
    df_consumption_reindexed = df_consumption_reindexed[
        (df_consumption_reindexed.index >= window_start)
        & (df_consumption_reindexed.index <= window_end)
    ]
    consumption_list = TotalConsumptionList(logger)
    for row in df_consumption_reindexed.itertuples():
        consumption_list.append(
            zoneKey=zone_key,
            consumption=row.consommation,
            datetime=row.Index.to_pydatetime(),
            source=SOURCE,
        )

    return consumption_list.to_list()
