#!/usr/bin/env python3

"""Real time parser for the state of New York."""
from collections import defaultdict
from datetime import timedelta
from operator import itemgetter
from urllib.error import HTTPError

import arrow
import pandas as pd

# Pumped storage is present but is not split into a separate category.
from arrow.parser import ParserError

from parsers.lib.config import refetch_frequency

# Dual Fuel systems can run either Natural Gas or Oil, they represent
# significantly more capacity in NY State than plants that can only
# burn Natural Gas. When looking up fuel usage for NY in 2016 in
# https://www.eia.gov/electricity/data/state/annual_generation_state.xls
# 100 times more energy came from NG than Oil. That means Oil
# consumption in the Dual Fuel systems is roughly ~1%, and to a first
# approximation it's just Natural Gas.


mapping = {
    "Dual Fuel": "gas",
    "Natural Gas": "gas",
    "Nuclear": "nuclear",
    "Other Fossil Fuels": "unknown",
    "Other Renewables": "unknown",
    "Wind": "wind",
    "Hydro": "hydro",
}


def read_csv_data(url):
    """Gets csv data from a url and returns a dataframe."""

    csv_data = pd.read_csv(url)

    return csv_data


def timestamp_converter(timestamp_string):
    """Converts timestamps in nyiso data into aware datetime objects."""
    try:
        dt_naive = arrow.get(timestamp_string, "MM/DD/YYYY HH:mm:ss")
    except ParserError:
        dt_naive = arrow.get(timestamp_string, "MM/DD/YYYY HH:mm")
    dt_aware = dt_naive.replace(tzinfo="America/New_York").datetime

    return dt_aware


def data_parser(df) -> list:
    """
    Takes dataframe and loops over rows to form dictionaries consisting of datetime and generation type.
    Merges these dictionaries using datetime key.

    :return: list of tuples containing datetime string and production.
    """

    chunks = []
    for row in df.itertuples():
        piece = {}
        piece["datetime"] = row[1]
        piece[row[3]] = row[4]
        chunks.append(piece)

    # Join dicts on shared 'datetime' keys.
    combine = defaultdict(dict)
    for elem in chunks:
        combine[elem["datetime"]].update(elem)

    ordered = sorted(combine.values(), key=itemgetter("datetime"))

    mapped_generation = []
    for item in ordered:
        mapped_types = [(mapping.get(k, k), v) for k, v in item.items()]

        # Need to avoid multiple 'unknown' keys overwriting.
        complete_production = defaultdict(lambda: 0.0)
        for key, val in mapped_types:
            try:
                complete_production[key] += val
            except TypeError:
                # Datetime is a string at this point!
                complete_production[key] = val

        dt = complete_production.pop("datetime")
        final = (dt, dict(complete_production))
        mapped_generation.append(final)

    return mapped_generation


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="US-NY", session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        # ensure we have an arrow object
        target_datetime = arrow.get(target_datetime)
    else:
        target_datetime = arrow.now("America/New_York")

    if (arrow.now() - target_datetime).days > 9:
        raise NotImplementedError(
            "you can get data older than 9 days at the "
            "url http://mis.nyiso.com/public/"
        )

    ny_date = target_datetime.format("YYYYMMDD")
    mix_url = "http://mis.nyiso.com/public/csv/rtfuelmix/{}rtfuelmix.csv".format(
        ny_date
    )
    try:
        raw_data = read_csv_data(mix_url)
    except HTTPError:
        # this can happen when target_datetime has no data available
        return None

    clean_data = data_parser(raw_data)

    production_mix = []
    for datapoint in clean_data:
        data = {
            "zoneKey": zone_key,
            "datetime": timestamp_converter(datapoint[0]),
            "production": datapoint[1],
            "storage": {},
            "source": "nyiso.com",
        }

        production_mix.append(data)

    return production_mix


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    url = (
        "http://mis.nyiso.com/public/csv/ExternalLimitsFlows/{}ExternalLimitsFlows.csv"
    )

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    # In the source CSV, positive is flow into NY, negative is flow out of NY.
    # In Electricity Map, A->B means flow to B is positive.
    if (
        sorted_zone_keys == "US-NEISO->US-NY"
        or sorted_zone_keys == "US-NE-ISNE->US-NY-NYIS"
    ):
        direction = 1
        relevant_exchanges = ["SCH - NE - NY", "SCH - NPX_1385", "SCH - NPX_CSC"]
    elif sorted_zone_keys == "US-NY->US-PJM":
        direction = -1
        relevant_exchanges = [
            "SCH - PJ - NY",
            "SCH - PJM_HTP",
            "SCH - PJM_NEPTUNE",
            "SCH - PJM_VFT",
        ]
    elif sorted_zone_keys == "US-MIDA-PJM->US-NY-NYIS":
        direction = 1
        relevant_exchanges = [
            "SCH - PJ - NY",
            "SCH - PJM_HTP",
            "SCH - PJM_NEPTUNE",
            "SCH - PJM_VFT",
        ]
    elif sorted_zone_keys == "CA-ON->US-NY" or sorted_zone_keys == "CA-ON->US-NY-NYIS":
        direction = 1
        relevant_exchanges = ["SCH - OH - NY"]
    elif sorted_zone_keys == "CA-QC->US-NY" or sorted_zone_keys == "CA-QC->US-NY-NYIS":
        direction = 1
        relevant_exchanges = ["SCH - HQ_CEDARS", "SCH - HQ - NY"]
    else:
        raise NotImplementedError(
            "Exchange pair not supported: {}".format(sorted_zone_keys)
        )

    if target_datetime:
        # ensure we have an arrow object
        target_datetime = arrow.get(target_datetime)
    else:
        target_datetime = arrow.now("America/New_York")
    ny_date = target_datetime.format("YYYYMMDD")
    exchange_url = url.format(ny_date)

    try:
        exchange_data = read_csv_data(exchange_url)
    except HTTPError:
        # this can happen when target_datetime has no data available
        return None

    new_england_exs = exchange_data.loc[
        exchange_data["Interface Name"].isin(relevant_exchanges)
    ]
    consolidated_flows = new_england_exs.reset_index().groupby("Timestamp").sum()

    now = arrow.utcnow()

    exchange_5min = []
    for row in consolidated_flows.itertuples():
        flow = float(row[3]) * direction
        # Timestamp for exchange does not include seconds.
        dt = timestamp_converter(row[0] + ":00")

        if (dt > now) and ((dt - now) < timedelta(seconds=300)):
            # NYISO exchanges CSV (and only the exchanges CSV) includes data
            # up to 5 minutes in the future (but only 5 minutes in the future).
            # This also happens on their official website.
            # Electricity Map raises error with data in the future, so skip
            # that datapoint. If it's more than 5 minutes in the future,
            # it's weird/unexpected and thus worthy of failure and logging.
            continue

        exchange = {
            "sortedZoneKeys": sorted_zone_keys,
            "datetime": dt,
            "netFlow": flow,
            "source": "nyiso.com",
        }

        exchange_5min.append(exchange)

    return exchange_5min


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())

    print('fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z")))

    print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z")))

    print("fetch_exchange(US-NY, US-NEISO)")
    pprint(fetch_exchange("US-NY", "US-NEISO"))

    print('fetch_exchange("US-NY", "CA-QC")')
    pprint(fetch_exchange("US-NY", "CA-QC"))

    print(
        'fetch_exchange("US-NY", "CA-QC", target_datetime=arrow.get("2018-03-13T12:00Z"))'
    )
    pprint(
        fetch_exchange("US-NY", "CA-QC", target_datetime=arrow.get("2018-03-13T12:00Z"))
    )

    print(
        'fetch_exchange("US-NY", "CA-QC", target_datetime=arrow.get("2007-03-13T12:00Z")))'
    )
    pprint(
        fetch_exchange("US-NY", "CA-QC", target_datetime=arrow.get("2007-03-13T12:00Z"))
    )
