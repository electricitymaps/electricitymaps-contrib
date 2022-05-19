#!/usr/bin/env python3

"""Parser for Bangladesh."""

import logging
from datetime import datetime

import arrow
import pandas as pd

GENERATION_MAPPING = {
    "Gas (Public)": "gas_public",
    "Gas (Private)": "gas_private",
    "Oil (Public)": "oil_public",
    "Oil (Private)": "oil_private",
    "Coal": "coal",
    "Hydro": "hydro",
    "Solar": "solar",
}


OLD_GENERATION_MAPPING = {
    "GAS": "gas_public",
    "P.GEN(GAS).": "gas_private",
    "OIL": "oil_public",
    "P.GEN(OIL).": "oil_private",
    "COAL": "coal",
    "HYDRO": "hydro",
    "SOLAR": "solar",
}


def timestamp_converter(raw_timestamp, target_datetime):
    """Converts string timestamp (e.g. 10:00:00) to arrow object."""

    hour, minute = raw_timestamp.split(":")[0:2]
    try:
        dt_aware = target_datetime.replace(
            hour=int(hour), minute=int(minute), tzinfo="Asia/Dhaka"
        )
    except ValueError:
        # 24:00 present in data, requires shifting forward.
        dt_aware = target_datetime.shift(days=+1)

    return dt_aware


def old_format_converter(df):
    """Returns a dataframe."""

    df = df.dropna(axis="columns", thresh=20)
    df = df.dropna(axis="index", thresh=4)
    df["TIME"] = df["TIME"].astype(str)
    df = df.reset_index(drop=True)
    df = df.set_index("TIME")

    return df


def new_format_converter(df, logger):
    """Returns a dataframe."""

    df = df.rename(columns={"Plant Name": "Hour"})
    df["Hour"] = df["Hour"].astype(str)
    df = df.reset_index(drop=True)
    df = df.set_index("Hour")
    total_index = df.columns.get_loc("Total (MW)")
    df = df.iloc[:, total_index:]

    try:
        time_index = df.index.get_loc("24:00")
    except KeyError:
        raise RuntimeError(
            "Structure of xlsm file for BD has altered, unable to parse."
        )

    df = df.iloc[: time_index + 1]

    # check for new columns
    if df.shape[1] != 12:
        logger.warning(
            "New data columns may be present xlsm file.", extra={"key": "BD"}
        )

    return df


def production_processer(df, target_datetime, old_format=False) -> list:
    """
    Takes dataframe and extracts all production data and timestamps.
    Returns a list of 2 element tuples in form (dict, arrow object).
    """

    if old_format:
        MAPPING = OLD_GENERATION_MAPPING
    else:
        MAPPING = GENERATION_MAPPING

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()
        dt = timestamp_converter(index, target_datetime)

        mapped_production = {
            MAPPING[k]: v for k, v in production.items() if k in MAPPING
        }
        mapped_production["gas"] = mapped_production.pop(
            "gas_public"
        ) + mapped_production.pop("gas_private")
        mapped_production["oil"] = mapped_production.pop(
            "oil_public"
        ) + mapped_production.pop("oil_private")
        processed_data.append((mapped_production, dt))

    return processed_data


def exchange_processer(df, target_datetime, old_format=False) -> list:
    """
    Takes dataframe and extracts all exchange data and timestamps.
    Returns a list of 2 element tuples in form (dict, arrow object).
    """

    # Positive means import from India hence sign reversal needed for EM.
    processed_data = []
    for index, row in df.iterrows():
        exchange = row.to_dict()
        flow = exchange.pop("HVDC", 0.0) + exchange.pop("Tripura", 0.0)
        dt = timestamp_converter(index, target_datetime)
        processed_data.append((-1 * flow, dt))

    return processed_data


def excel_handler(shifted_target_datetime, logger) -> tuple:
    """
    Decides which url to request based on supplied arrow object.
    Converts returned excel data into dataframe, format of data varies by date.
    Returns a tuple containing (dataframe, bool).
    """

    # NOTE file named 11-01-2019 actually covers 10-01-2019, pattern repeats!
    # xls structure very different pre 11-01-18
    # Before 03-07-2015 it's Daily_Report not Daily Report
    # File name format adds space on 11-01-18
    # Odd format around this time (XLS_SPAN)
    # However file ending changes several days later! (╯°□°）╯︵ ┻━┻

    OLD_FORMAT = False
    if shifted_target_datetime <= arrow.get("20180111", "YYYYMMDD"):
        OLD_FORMAT = True

    XLS_SPAN = (datetime(2018, 1, 12), datetime(2018, 1, 13), datetime(2018, 1, 14))

    XLS_END = False
    if shifted_target_datetime.naive in XLS_SPAN:
        XLS_END = True

    UNDERSCORE = False
    if shifted_target_datetime <= arrow.get("20150703", "YYYYMMDD"):
        UNDERSCORE = True

    day = shifted_target_datetime.format("DD")
    month = shifted_target_datetime.format("MM")
    short_year = shifted_target_datetime.format("YY")

    # NOTE %20 padders needed, format is day-month-year
    if OLD_FORMAT and UNDERSCORE:
        URL = "https://pgcb.org.bd/PGCB/upload/Reports/Daily_Report{}-{}-{}.xls".format(
            day, month, short_year
        )
    elif OLD_FORMAT:
        URL = (
            "https://pgcb.org.bd/PGCB/upload/Reports/Daily%20Report{}-{}-{}.xls".format(
                day, month, short_year
            )
        )
    elif XLS_END:
        URL = "https://pgcb.org.bd/PGCB/upload/Reports/Daily%20Report%20{}-{}-{}.xls".format(
            day, month, short_year
        )
    else:
        URL = "https://pgcb.org.bd/PGCB/upload/Reports/Daily%20Report%20{}-{}-{}.xlsm".format(
            day, month, short_year
        )

    if OLD_FORMAT:
        df = pd.read_excel(URL, sheet_name="En.Curve", skiprows=[0, 1, 2, 3])
        df = old_format_converter(df)
    else:
        if XLS_END:
            df = pd.read_excel(
                URL,
                sheet_name="YesterdayGen",
                skiprows=[0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            )
            df = new_format_converter(df, logger)
        else:
            df = pd.read_excel(URL, sheet_name="YesterdayGen", skiprows=[0, 1, 3])
            df = new_format_converter(df, logger)

    return df, OLD_FORMAT


def fetch_production(
    zone_key="BD",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""

    if not target_datetime:
        raise NotImplementedError(
            """This parser is only able to get historical
                                  data up to the previous day, please pass a
                                  target_datetime in format YYYYMMDD."""
        )

    target_datetime = arrow.get(target_datetime, "YYYYMMDD")
    shifted_target_datetime = target_datetime.shift(days=+1)

    df, OLD_FORMAT = excel_handler(shifted_target_datetime, logger)

    generation = production_processer(df, target_datetime, old_format=OLD_FORMAT)

    data = []
    for item in generation:
        datapoint = {
            "zoneKey": zone_key,
            "datetime": item[1].datetime,
            "production": item[0],
            "storage": {},
            "source": "pgcb.org.bd",
        }

        data.append(datapoint)

    return data


def fetch_exchange(
    zone_key1,
    zone_key2,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    if not target_datetime:
        raise NotImplementedError(
            """This parser is only able to get historical
                                  data up to the previous day, please pass a
                                  target_datetime in format YYYYMMDD."""
        )

    sorted_codes = "->".join(sorted([zone_key1, zone_key2]))

    target_datetime = arrow.get(target_datetime, "YYYYMMDD")
    shifted_target_datetime = target_datetime.shift(days=+1)

    df, OLD_FORMAT = excel_handler(shifted_target_datetime, logger)
    exchange = exchange_processer(df, target_datetime, old_format=OLD_FORMAT)

    data = []
    for item in exchange:
        datapoint = {
            "sortedZoneKeys": sorted_codes,
            "datetime": item[1].datetime,
            "netFlow": item[0],
            "source": "pgcb.org.bd",
        }

        data.append(datapoint)

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production(target_datetime=20190110)")
    print(fetch_production(target_datetime="20190110"))
    print("fetch_production(target_datetime=20180113)")
    print(fetch_production(target_datetime="20180113"))
    print("fetch_production(target_datetime=20170110)")
    print(fetch_production(target_datetime="20170110"))
    print("fetch_production(target_datetime=20150601)")
    print(fetch_production(target_datetime="20150601"))
    print("fetch_exchange(target_datetime=20190109)")
    print(fetch_exchange("BD", "IN", target_datetime="20190109"))
    print("fetch_exchange(target_datetime=20170109)")
    print(fetch_exchange("BD", "IN", target_datetime="20170109"))
    print("fetch_exchange(target_datetime=20150109)")
    print(fetch_exchange("BD", "IN", target_datetime="20150109"))
