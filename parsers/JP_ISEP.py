#!/usr/bin/env python3
import datetime
import json
import logging
import os
import re

import pandas as pd
import requests

url = "https://isep-energychart.com/en/graphics/electricityproduction/?region={region}&period_year={year}&period_month={month}&period_day={day}&period_length=1day&display_format=residual_demand"
timezone = "Japan"

MAP_ZONE_TO_REGION_NAME = {
    "JP": "all",
    "JP-HKD": "hokkaido",
    "JP-TH": "tohoku",
    "JP-TK": "tokyo",
    "JP-CB": "chubu",
    "JP-HR": "hokuriku",
    "JP-KN": "kansai",
    "JP-CG": "chugoku",
    "JP-SK": "shikoku",
    "JP-KY": "kyushu",
    "JP-ON": "okinawa",
}

COLUMN_MAP = {
    "demand": "consumption",
    "wind_performance": "wind",
    "solar_performance": "solar",
    "thermal": "unknown",
    "pumped": "pumped hydro",
    "interconnection": "exchanges",
    "solar_suppression": "solar curtailment",
    "wind_suppression": "wind curtailment",
}


def get_data(region, year, month, day):
    r = requests.get(url.format(region=region, year=year, month=month, day=day))

    assert r.status_code == 200, "Could not get url"

    jsonval_matches = re.findall(
        "(?<=var jsonval = JSON.parse\(').*(?='\)\n\t)", r.text
    )
    assert len(
        jsonval_matches
    ), "Data not found. Perhaps the format of the html file has changed, or data for this date is not yet available?"

    df = pd.read_json(jsonval_matches[0])

    return df


def process_data(df):
    # convert to timestamp with timezone info
    df["date_time"] = (
        pd.to_datetime(df["date_time"]).dt.tz_localize(timezone).dt.tz_convert("UTC")
    )

    df = df.rename(columns=COLUMN_MAP)

    df["hydro storage"] = df["pumped hydro"].map(lambda x: x if x < 0 else 0)
    df["hydro discharge"] = df["pumped hydro"].map(lambda x: x if x > 0 else 0)

    # Should be removed if we ever handle curtailment data separately
    if "wind" in df.columns:
        df["wind adjusted"] = df["wind"] + df.get("wind curtailment", 0)

    if "solar" in df.columns:
        df["solar adjusted"] = df["solar"] + df.get("solar curtailment", 0)
    return df


def fetch_production(
    zone_key="JP",
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the historic production mix (in MW) of japan."""
    if target_datetime is None:
        # This data is only available with approx 4 month delay
        raise NotImplementedError(
            "target_datetime must be provided, this parser can only parse historic data"
        )

    region = MAP_ZONE_TO_REGION_NAME[zone_key]

    year = target_datetime.year
    month = target_datetime.month
    day = target_datetime.day

    df = get_data(region, year, month, day)
    df = process_data(df)

    data = []
    for name, row in df.iterrows():
        dat = {
            "datetime": row["date_time"].to_pydatetime(),
            "zoneKey": zone_key,
            "production": {
                "biomass": row.get("biomass", None),
                "hydro": row.get("hydro", None),
                "hydro discharge": row.get("hydro discharge", None),
                "nuclear": row.get("nuclear", None),
                "solar": row.get("solar adjusted", None),
                "wind": row.get("wind adjusted", None),
                "geothermal": row.get("geothermal", None),
                "unknown": row.get("unknown", None),
            },
            "storage": {"hydro": row.get("hydro storage", None)},
            "source": "isep-energychart.com",
        }
        data += [dat]

    return data


def fetch_consumption(
    zone_key="JP",
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the historic consumption mix (in MW) of japan."""
    if target_datetime is None:
        # This data is only available with approx 4 month delay
        raise NotImplementedError(
            "target_datetime must be provided, this parser can only parse historic data"
        )

    region = MAP_ZONE_TO_REGION_NAME[zone_key]

    year = target_datetime.year
    month = target_datetime.month
    day = target_datetime.day

    df = get_data(region, year, month, day)
    df = process_data(df)

    data = []
    for name, row in df.iterrows():
        dat = {
            "datetime": row["date_time"].to_pydatetime(),
            "zoneKey": zone_key,
            "consumption": row.get("consumption", None),
            "source": "isep-energychart.com",
        }
        data += [dat]

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production(target_datetime=pd.Timestamp("2019-01-01")))
    print("fetch_consumption() ->")
    print(fetch_consumption(target_datetime=pd.Timestamp("2019-01-01")))
