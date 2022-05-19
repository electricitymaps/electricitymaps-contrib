#!/usr/bin/env python3

"""Parser for the Bonneville Power Administration area of the USA."""


import logging
from io import StringIO

import arrow
import pandas as pd
import requests

GENERATION_URL = "https://transmission.bpa.gov/business/operations/Wind/baltwg.txt"

GENERATION_MAPPING = {
    "Wind": "wind",
    "Hydro": "hydro",
    "Fossil/Biomass": "unknown",
    "Nuclear": "nuclear",
}


def get_data(url, session=None):
    """Returns a pandas dataframe."""
    s = session or requests.Session()
    req = s.get(url)
    df = pd.read_table(StringIO(req.text), skiprows=11)

    return df


def timestamp_converter(timestamp):
    """Turns a timestamp str into an aware datetime object."""

    arr_dt_naive = arrow.get(timestamp, "MM/DD/YYYY HH:mm")
    dt_aware = arr_dt_naive.replace(tzinfo="America/Los_Angeles").datetime

    return dt_aware


def data_processor(df, logger) -> list:
    """
    Takes a dataframe and drops all generation rows that are empty or more than 1 day old.
    Turns each row into a dictionary and removes any generation types that are unknown.

    :return: list of tuples in the form of (datetime, production).
    """

    df = df.dropna(thresh=2)
    df.columns = df.columns.str.strip()

    # 5min data for the last 24 hours.
    df = df.tail(288)
    df["Date/Time"] = df["Date/Time"].map(timestamp_converter)

    known_keys = GENERATION_MAPPING.keys() | {"Date/Time", "Load"}
    column_headers = set(df.columns)

    unknown_keys = column_headers - known_keys

    for k in unknown_keys:
        logger.warning(
            "New data {} seen in US-BPA data source".format(k), extra={"key": "US-BPA"}
        )

    keys_to_remove = unknown_keys | {"Load"}

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()

        dt = production.pop("Date/Time")
        dt = dt.to_pydatetime()
        mapped_production = {
            GENERATION_MAPPING[k]: v
            for k, v in production.items()
            if k not in keys_to_remove
        }

        processed_data.append((dt, mapped_production))

    return processed_data


def fetch_production(
    zone_key="US-BPA",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    raw_data = get_data(GENERATION_URL, session=session)
    processed_data = data_processor(raw_data, logger)

    data = []
    for item in processed_data:
        datapoint = {
            "zoneKey": zone_key,
            "datetime": item[0],
            "production": item[1],
            "storage": {},
            "source": "bpa.gov",
        }

        data.append(datapoint)

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
