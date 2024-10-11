#!/usr/bin/env python3

from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import numpy as np
import pandas
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency

CAISO_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
PRODUCTION_URL_REAL_TIME = (
    f"{CAISO_PROXY}/outlook/SP/fuelsource.csv?host=https://www.caiso.com"
)
DEMAND_URL_REAL_TIME = (
    f"{CAISO_PROXY}/outlook/SP/netdemand.csv?host=https://www.caiso.com"
)

HISTORICAL_URL_MAPPING = {"production": "fuelsource", "consumption": "netdemand"}
REAL_TIME_URL_MAPPING = {
    "production": PRODUCTION_URL_REAL_TIME,
    "consumption": DEMAND_URL_REAL_TIME,
}

PRODUCTION_MODES_MAPPING = {
    "solar": "solar",
    "wind": "wind",
    "geothermal": "geothermal",
    "biomass": "biomass",
    "biogas": "biomass",
    "small hydro": "hydro",
    "coal": "coal",
    "nuclear": "nuclear",
    "natural gas": "gas",
    "large hydro": "hydro",
    "other": "unknown",
}

CORRECT_NEGATIVE_PRODUCTION_MODES_WITH_ZERO = [
    mode
    for mode in PRODUCTION_MODES_MAPPING
    if mode not in ["large hydro", "small hydro"]
]
STORAGE_MAPPING = {"batteries": "battery"}

TIMEZONE = ZoneInfo("US/Pacific")


def get_target_url(target_datetime: datetime | None, kind: str) -> str:
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
        target_url = REAL_TIME_URL_MAPPING[kind]
    else:
        target_url = f"{CAISO_PROXY}/outlook/SP/History/{target_datetime.strftime('%Y%m%d')}/{HISTORICAL_URL_MAPPING[kind]}.csv?host=https://www.caiso.com"
    return target_url


def add_production_to_dict(mode: str, value: float, production_dict: dict) -> dict:
    """Add production to production_dict, if mode is in PRODUCTION_MODES."""
    if PRODUCTION_MODES_MAPPING[mode] not in production_dict:
        production_dict[PRODUCTION_MODES_MAPPING[mode]] = value
    else:
        production_dict[PRODUCTION_MODES_MAPPING[mode]] += value
    return production_dict


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("US-CAL-CISO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    target_url = get_target_url(target_datetime, kind="production")

    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Get the production from the CSV
    csv = pandas.read_csv(target_url)

    # Filter out last row if timestamp is 00:00
    df = csv.copy().iloc[:-1] if csv.iloc[-1]["Time"] == "OO:OO" else csv.copy()

    # lower case column names
    df.columns = [col.lower() for col in df.columns]

    all_data_points = ProductionBreakdownList(logger)
    for _index, row in df.iterrows():
        production_mix = ProductionMix()
        storage_mix = StorageMix()
        row_datetime = target_datetime.replace(
            hour=int(row["time"][:2]), minute=int(row["time"][-2:]), tzinfo=TIMEZONE
        )

        for mode in [
            mode
            for mode in PRODUCTION_MODES_MAPPING
            if mode not in ["small hydro", "large hydro"]
        ]:
            production_value = float(row[mode])
            production_mix.add_value(
                PRODUCTION_MODES_MAPPING[mode],
                production_value,
                mode in CORRECT_NEGATIVE_PRODUCTION_MODES_WITH_ZERO,
            )

        for mode in ["small hydro", "large hydro"]:
            production_value = float(row[mode])
            if production_value < 0:
                storage_mix.add_value("hydro", production_value * -1)
            else:
                production_mix.add_value("hydro", production_value)

        storage_mix.add_value("battery", float(row["batteries"]) * -1)
        all_data_points.append(
            zoneKey=zone_key,
            production=production_mix,
            storage=storage_mix,
            source="caiso.com",
            datetime=row_datetime,
        )

    return all_data_points.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("US-CAL-CISO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""

    target_url = get_target_url(target_datetime, kind="consumption")

    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    # Get the demand from the CSV
    csv = pandas.read_csv(target_url)

    # Filter out last row if timestamp is 00:00
    df = csv.copy().iloc[:-1] if csv.iloc[-1]["Time"] == "OO:OO" else csv.copy()

    all_data_points = TotalConsumptionList(logger)
    for row in df.itertuples():
        consumption = row._3
        row_datetime = target_datetime.replace(
            hour=int(row.Time[:2]), minute=int(row.Time[-2:]), tzinfo=TIMEZONE
        )
        if not np.isnan(consumption):
            all_data_points.append(
                zoneKey=zone_key,
                consumption=consumption,
                source="caiso.com",
                datetime=row_datetime,
            )

    return all_data_points.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    # CSV has imports to California as positive.
    # Electricity Map expects A->B to indicate flow to B as positive.
    # So values in CSV can be used as-is.
    target_url = get_target_url(target_datetime, kind="production")
    csv = pandas.read_csv(target_url)
    latest_index = len(csv) - 1
    daily_data = []
    for i in range(0, latest_index + 1):
        h, m = map(int, csv["Time"][i].split(":"))
        date = datetime.now(tz=TIMEZONE).replace(
            hour=h, minute=m, second=0, microsecond=0
        )
        data = {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": date,
            "netFlow": float(csv["Imports"][i]),
            "source": "caiso.com",
        }

        daily_data.append(data)

    return daily_data


if __name__ == "__main__":
    "Main method, not used by Electricity Map backend, but handy for testing"

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production(target_datetime=datetime(2020, 1, 20)))

    print('fetch_exchange("US-CA", "US") ->')
    # pprint(fetch_exchange("US-CA", "US"))

    # pprint(fetch_production(target_datetime=datetime(2023,1,20)))s
    pprint(fetch_consumption(target_datetime=datetime(2022, 2, 22)))
