#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""

import datetime
from io import StringIO
from logging import getLogger

import pandas as pd
import requests
from dateutil import parser, tz
from pandas.tseries.offsets import DateOffset

from parsers.lib.config import refetch_frequency

HISTORIC_GENERATION_BASE_URL = "https://marketplace.spp.org/file-browser-api/download/generation-mix-historical?path=%2F"

GENERATION_URL = "https://marketplace.spp.org/chart-api/gen-mix/asFile"

EXCHANGE_URL = "https://marketplace.spp.org/chart-api/interchange-trend/asFile"

MAPPING = {
    "Wind": "wind",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
    "Solar": "solar",
    "Natural Gas": "gas",
    "Diesel Fuel Oil": "oil",
    "Waste Disposal Services": "biomass",
    "Coal": "coal",
}

TIE_MAPPING = {"US-MISO->US-SPP": ["AMRN", "DPC", "GRE", "MDU", "MEC", "NSP", "OTP"]}

# NOTE
# Data sources return timestamps in GMT.
# Energy storage situation unclear as of 16/03/2018, likely to change quickly in future.


def get_data(url, session=None):
    """Returns a pandas dataframe."""

    s = session or requests.Session()
    req = s.get(url, verify=False)
    df = pd.read_csv(StringIO(req.text))

    return df


def data_processor(df, logger) -> list:
    """
    Takes a dataframe and logging instance as input.
    Checks for new generation types and logs a warning if any are found.
    Parses the dataframe row by row removing unneeded keys.

    :return: list of tuples containing a datetime object and production dictionary.
    """

    # Remove leading whitespace in column headers.
    df.columns = df.columns.str.strip()
    df = df.rename(
        columns={"Gas Self": "Natural Gas Self"}
    )  # Fix naming error which otherwise misclassifies Gas Self as Unknown
    # Some historical csvs split the production into 'Market' and 'Self',
    # So first we need to combine those.
    for col in df.columns:
        if "Market" in col:
            combined_col = col.replace("Market", "").strip()
            self_col = col.replace("Market", "Self")
            if self_col in df.columns:
                df[combined_col] = df[col] + df[self_col]
                df.drop(self_col, inplace=True, axis=1)
            else:
                logger.warning(
                    f'Corresponding column "{self_col}" to "{col}" not found in file',
                    extra={"key": "US-SPP"},
                )
                df[combined_col] = df[col]

            df.drop(col, inplace=True, axis=1)

    keys_to_remove = {"GMT MKT Interval", "Average Actual Load", "Load"}

    # Check for new generation columns.
    known_keys = MAPPING.keys() | keys_to_remove
    column_headers = set(df.columns)

    unknown_keys = column_headers - known_keys

    for heading in unknown_keys:
        if heading not in ["Other", "Waste Heat"]:
            logger.warning(
                "New column '{}' present in US-SPP data source.".format(heading),
                extra={"key": "US-SPP"},
            )

    keys_to_remove = keys_to_remove | unknown_keys

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()
        production["unknown"] = sum([production[k] for k in unknown_keys])

        dt_aware = production["GMT MKT Interval"].to_pydatetime()
        for k in keys_to_remove:
            production.pop(k, None)

        mapped_production = {MAPPING.get(k, k): v for k, v in production.items()}

        processed_data.append((dt_aware, mapped_production))
    return processed_data


@refetch_frequency(datetime.timedelta(days=1))
def fetch_production(
    zone_key="US-SPP", session=None, target_datetime=None, logger=getLogger(__name__)
) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime is not None:
        current_year = datetime.datetime.now().year
        target_year = target_datetime.year

        # Check if datetime is too far in the past
        if target_year < 2011:
            raise NotImplementedError("Data before 2011 not available from this source")

        # Check if datetime in current year, or past year
        if target_year == current_year:
            filename = "GenMixYTD.csv"
        else:
            filename = f"GenMix_{target_year}.csv"

        historic_generation_url = HISTORIC_GENERATION_BASE_URL + filename
        raw_data = get_data(historic_generation_url, session=session)
        # In some cases the timeseries column is named differently, so we standardize it
        raw_data.rename(columns={"GMTTime": "GMT MKT Interval"}, inplace=True)

        raw_data["GMT MKT Interval"] = pd.to_datetime(
            raw_data["GMT MKT Interval"], utc=True
        )
        end = target_datetime
        start = target_datetime - datetime.timedelta(days=1)
        start = max(start, raw_data["GMT MKT Interval"].min())
        raw_data = raw_data[
            (raw_data["GMT MKT Interval"] >= start)
            & (raw_data["GMT MKT Interval"] <= end)
        ]
    else:
        raw_data = get_data(GENERATION_URL, session=session)
        raw_data["GMT MKT Interval"] = pd.to_datetime(raw_data["GMT MKT Interval"])

    processed_data = data_processor(raw_data, logger)

    data = []
    for item in processed_data:
        dt = item[0].replace(tzinfo=tz.gettz("Etc/GMT"))
        datapoint = {
            "zoneKey": zone_key,
            "datetime": dt,
            "production": item[1],
            "storage": {},
            "source": "spp.org",
        }
        data.append(datapoint)

    return data


# NOTE disabled until discrepancy in MISO SPP flows is resolved.
def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=getLogger(__name__)
) -> list:
    """
    Requests the last 24 hours of power exchange (in MW) between two zones."""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    raw_data = get_data(EXCHANGE_URL, session=session)
    sorted_codes = "->".join(sorted([zone_key1, zone_key2]))

    try:
        exchange_ties = TIE_MAPPING[sorted_codes]
    except KeyError as e:
        raise NotImplementedError(
            "The exchange {} is not implemented".format(sorted_codes)
        )

    # TODO check glossary for flow direction.

    exchange_data = []
    for index, row in raw_data.iterrows():
        all_exchanges = row.to_dict()

        dt_aware = parser.parse(all_exchanges["GMTTime"])

        flows = [all_exchanges[tie] for tie in exchange_ties]
        netflow = sum(flows)

        exchange = {
            "sortedZoneKeys": sorted_codes,
            "datetime": dt_aware,
            "netFlow": netflow,
            "source": "spp.org",
        }

        exchange_data.append(exchange)

    return exchange_data


def fetch_load_forecast(
    zone_key="US-SPP", session=None, target_datetime=None, logger=getLogger(__name__)
) -> list:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.datetime.now()

    if isinstance(target_datetime, datetime.datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    LOAD_URL = "https://marketplace.spp.org/file-api/download/mtlf-vs-actual?path=%2F{0}%2F{1:02d}%2F{2:02d}%2FOP-MTLF-{0}{1:02d}{2:02d}0000.csv".format(
        dt.year, dt.month, dt.day
    )

    raw_data = get_data(LOAD_URL)

    data = []
    for index, row in raw_data.iterrows():
        forecast = row.to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(
            tzinfo=tz.gettz("Etc/GMT")
        )
        load = float(forecast["MTLF"])

        datapoint = {
            "datetime": dt,
            "value": load,
            "zoneKey": zone_key,
            "source": "spp.org",
        }

        data.append(datapoint)

    return data


@refetch_frequency(datetime.timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key="US-SPP", session=None, target_datetime=None, logger=getLogger(__name__)
) -> list:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.datetime.now()

    if isinstance(target_datetime, datetime.datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    FORECAST_URL = "https://marketplace.spp.org/file-browser-api/download/midterm-resource-forecast?path=%2F{0}%2F{1:02d}%2F{2:02d}%2FOP-MTRF-{0}{1:02d}{2:02d}0000.csv".format(
        dt.year, dt.month, dt.day
    )

    raw_data = get_data(FORECAST_URL)

    # sometimes there is a leading whitespace in column names
    raw_data.columns = raw_data.columns.str.lstrip()

    data = []
    for index, row in raw_data.iterrows():
        forecast = row.to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(
            tzinfo=tz.gettz("Etc/GMT")
        )

        try:
            solar = float(forecast["Wind Forecast MW"])
            wind = float(forecast["Solar Forecast MW"])
        except ValueError:
            # can be NaN
            continue

        datapoint = {
            "datetime": dt,
            "production": {
                "solar": solar,
                "wind": wind,
            },
            "zoneKey": zone_key,
            "source": "spp.org",
        }

        data.append(datapoint)

    return data


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production())
    # print('fetch_exchange() -> ')
    # print(fetch_exchange('US-MISO', 'US-SPP'))
    print("fetch_load_forecast() -> ")
    print(fetch_load_forecast(target_datetime="20190125"))
    print("fetch_wind_solar_forecasts() -> ")
    print(fetch_wind_solar_forecasts(target_datetime="20190125"))
