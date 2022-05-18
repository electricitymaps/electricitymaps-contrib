#!/usr/bin/env python3
# coding=utf-8

"""
Parser that uses the ELEXON API to return the following data types.

Production
Exchanges

Documentation:
https://www.elexon.co.uk/wp-content/uploads/2017/06/
bmrs_api_data_push_user_guide_v1.1.pdf
"""

import datetime as dt
import logging
from io import StringIO

import arrow
import pandas as pd
import requests

from parsers.lib.config import refetch_frequency

from .lib.utils import get_token
from .lib.validation import validate

ELEXON_ENDPOINT = "https://api.bmreports.com/BMRS/{}/v1"

REPORT_META = {
    "B1620": {"expected_fields": 13, "skiprows": 5},
    "FUELINST": {"expected_fields": 22, "skiprows": 1},
    "INTERFUELHH": {"expected_fields": 11, "skiprows": 0},
}

# 'hydro' key is for hydro production
# 'hydro storage' key is for hydro storage
RESOURCE_TYPE_TO_FUEL = {
    "Biomass": "biomass",
    "Fossil Gas": "gas",
    "Fossil Hard coal": "coal",
    "Fossil Oil": "oil",
    "Hydro Pumped Storage": "hydro storage",
    "Hydro Run-of-river and poundage": "hydro",
    "Nuclear": "nuclear",
    "Solar": "solar",
    "Wind Onshore": "wind",
    "Wind Offshore": "wind",
    "Other": "unknown",
}

EXCHANGES = {
    "FR->GB": [3, 8, 9],  # IFA, Eleclink, IFA2
    "GB->GB-NIR": [4],
    "GB->NL": [5],
    "GB->IE": [6],
    "BE->GB": [7],
    "GB->NO-NO2": [10],  # North Sea Link
}

FETCH_WIND_FROM_FUELINST = True


def query_ELEXON(report, session, params):
    params["APIKey"] = get_token("ELEXON_TOKEN")
    return session.get(ELEXON_ENDPOINT.format(report), params=params)


def query_exchange(session, target_datetime=None):
    if target_datetime is None:
        target_datetime = dt.date.today()

    from_date = (target_datetime - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = target_datetime.strftime("%Y-%m-%d")

    params = {"FromDate": from_date, "ToDate": to_date, "ServiceType": "csv"}
    response = query_ELEXON("INTERFUELHH", session, params)
    return response.text


def query_production(session, target_datetime=None):
    if target_datetime is None:
        target_datetime = dt.datetime.now()

    # we can only fetch one date at a time.
    # if target_datetime is first 30 minutes of the day fetch the day before.
    # otherwise fetch the day of target_datetime.
    if target_datetime.time() <= dt.time(0, 30):
        settlement_date = target_datetime.date() - dt.timedelta(1)
    else:
        settlement_date = target_datetime.date()

    params = {
        "SettlementDate": settlement_date.strftime("%Y-%m-%d"),
        "Period": "*",
        "ServiceType": "csv",
    }
    response = query_ELEXON("B1620", session, params)
    return response.text


def parse_exchange(
    zone_key1,
    zone_key2,
    csv_text,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if not csv_text:
        return None

    report = REPORT_META["INTERFUELHH"]

    sorted_zone_keys = sorted([zone_key1, zone_key2])
    exchange = "->".join(sorted_zone_keys)
    data_points = list()
    lines = csv_text.split("\n")

    # check field count in report is as expected
    field_count = len(lines[1].split(","))
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in INTERFUELHH report, got {}".format(
                report["expected_fields"], field_count
            )
        )

    for line in lines[1:-1]:
        fields = line.split(",")

        # settlement date / period combinations are always local time
        date = dt.datetime.strptime(fields[1], "%Y%m%d").date()
        settlement_period = int(fields[2])
        datetime = datetime_from_date_sp(date, settlement_period)

        data = {
            "sortedZoneKeys": exchange,
            "datetime": datetime,
            "source": "bmreports.com",
        }

        # positive value implies import to GB
        multiplier = -1 if "GB" in sorted_zone_keys[0] else 1
        net_flow = 0.0  # init
        for column_index in EXCHANGES[exchange]:
            # read out all columns providing values for this exchange
            if fields[column_index] == "":
                continue  # no value provided for this exchange
            net_flow += float(fields[column_index]) * multiplier
        data["netFlow"] = net_flow
        data_points.append(data)

    return data_points


def parse_production(
    csv_text, target_datetime=None, logger=logging.getLogger(__name__)
):
    if not csv_text:
        return None

    report = REPORT_META["B1620"]

    # create DataFrame from slice of CSV rows
    df = pd.read_csv(StringIO(csv_text), skiprows=report["skiprows"] - 1)

    # check field count in report is as expected
    field_count = len(df.columns)
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in B1620 report, got {}".format(
                report["expected_fields"], len(df.columns)
            )
        )

    # filter out undesired columns
    df = df.iloc[:-1, [7, 8, 9, 4]]

    df["Settlement Date"] = df["Settlement Date"].apply(
        lambda x: dt.datetime.strptime(x, "%Y-%m-%d")
    )
    df["Settlement Period"] = df["Settlement Period"].astype(int)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["Settlement Date"], x["Settlement Period"]),
        axis=1,
    )

    # map from report fuel names to electricitymap fuel names
    fuel_column = "Power System Resource  Type"
    df[fuel_column] = df[fuel_column].apply(lambda x: RESOURCE_TYPE_TO_FUEL[x])

    # loop through unique datetimes and create each data point
    data_points = list()
    for time in pd.unique(df["datetime"]):
        time_df = df[df["datetime"] == time]

        data_point = {
            "zoneKey": "GB",
            "datetime": time.to_pydatetime(),
            "source": "bmreports.com",
            "production": dict(),
            "storage": dict(),
        }

        for row in time_df.iterrows():
            fields = row[1].to_dict()
            fuel = fields[fuel_column]
            quantity = fields["Quantity"]

            # check if storage value and if so correct key
            if "storage" in fuel:
                fuel_key = fuel.replace("storage", "").strip()
                # ELEXON storage is negative when storing and positive when
                # discharging (the opposite to electricitymap)
                data_point["storage"][fuel_key] = quantity * -1
            else:
                # if/else structure allows summation of multiple quantities
                # e.g. 'Wind Onshore' and 'Wind Offshore' both have the
                # key 'wind' here.
                if fuel in data_point["production"].keys():
                    data_point["production"][fuel] += quantity
                else:
                    data_point["production"][fuel] = quantity

        data_points.append(data_point)

    return data_points


def datetime_from_date_sp(date, sp):
    datetime = arrow.get(date).shift(minutes=30 * (sp - 1))
    return datetime.replace(tzinfo="Europe/London").datetime


def _fetch_wind(target_datetime=None):
    if target_datetime is None:
        target_datetime = dt.datetime.now()

    # line up with B1620 (main production report) search range
    d = target_datetime.date()
    start = d - dt.timedelta(hours=48)
    end = dt.datetime.combine(d + dt.timedelta(days=1), dt.time(0))

    session = requests.session()
    params = {
        "FromDateTime": start.strftime("%Y-%m-%d %H:%M:%S"),
        "ToDateTime": end.strftime("%Y-%m-%d %H:%M:%S"),
        "ServiceType": "csv",
    }
    response = query_ELEXON("FUELINST", session, params)
    csv_text = response.text

    report = REPORT_META["FUELINST"]
    df = pd.read_csv(
        StringIO(csv_text), skiprows=report["skiprows"], skipfooter=1, header=None
    )

    field_count = len(df.columns)
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in FUELINST report, got {}".format(
                report["expected_fields"], len(df.columns)
            )
        )

    df = df.iloc[:, [1, 2, 3, 8]]
    df.columns = ["Settlement Date", "Settlement Period", "published", "Wind"]
    df["Settlement Date"] = df["Settlement Date"].apply(
        lambda x: dt.datetime.strptime(str(x), "%Y%m%d")
    )
    df["Settlement Period"] = df["Settlement Period"].astype(int)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["Settlement Date"], x["Settlement Period"]),
        axis=1,
    )

    df["published"] = df["published"].apply(
        lambda x: dt.datetime.strptime(str(x), "%Y%m%d%H%M%S")
    )
    # get the most recently published value for each datetime
    idx = df.groupby("datetime")["published"].transform(max) == df["published"]
    df = df[idx]

    return df[["datetime", "Wind"]]


@refetch_frequency(dt.timedelta(days=1))
def fetch_exchange(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    session = session or requests.session()
    response = query_exchange(session, target_datetime)
    data = parse_exchange(zone_key1, zone_key2, response, target_datetime, logger)
    return data


@refetch_frequency(dt.timedelta(days=1))
def fetch_production(
    zone_key="GB",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    session = session or requests.session()
    response = query_production(session, target_datetime)
    data = parse_production(response, target_datetime, logger)

    # At times B1620 has had poor quality data for wind so fetch from FUELINST
    if FETCH_WIND_FROM_FUELINST:
        wind = _fetch_wind(target_datetime)
        for entry in data:
            datetime = entry["datetime"]
            wind_row = wind[wind["datetime"] == datetime]
            if len(wind_row):
                entry["production"]["wind"] = wind_row.iloc[0]["Wind"]
            else:
                entry["production"]["wind"] = None

    required = ["coal", "gas", "nuclear", "wind"]
    expected_range = {
        "coal": (0, 10000),
        "gas": (100, 30000),
        "nuclear": (100, 20000),
        "wind": (0, 30000),
    }
    data = [
        x
        for x in data
        if validate(x, logger, required=required, expected_range=expected_range)
    ]

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_exchange(FR, GB) ->")
    print(fetch_exchange("FR", "GB"))

    print("fetch_exchange(GB, IE) ->")
    print(fetch_exchange("GB", "IE"))

    print("fetch_exchange(GB, NL) ->")
    print(fetch_exchange("GB", "NL"))
