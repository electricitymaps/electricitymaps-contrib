#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""


from datetime import datetime, timedelta
from io import StringIO
from logging import Logger, getLogger
from typing import Optional

from pytz import utc
import pandas as pd
from dateutil import parser, tz
from requests import Session

from parsers.lib.config import refetch_frequency

US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "host=https://marketplace.spp.org"

HISTORIC_GENERATION_BASE_URL = f"{US_PROXY}/file-browser-api/download/generation-mix-historical?{HOST_PARAMETER}&path="

GENERATION_URL = f"{US_PROXY}/chart-api/gen-mix/asFile?{HOST_PARAMETER}"

EXCHANGE_URL = f"{US_PROXY}/chart-api/interchange-trend/asFile?{HOST_PARAMETER}"

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


def get_data(url, session: Optional[Session] = None):
    """Returns a pandas dataframe."""

    s = session or Session()
    req = s.get(url, verify=False)
    df = pd.read_csv(StringIO(req.text))

    return df


def data_processor(df, logger: Logger) -> list:
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
    for index in range(len(df)):
        production = df.loc[index].to_dict()
        production["unknown"] = sum([production[k] for k in unknown_keys])

        dt_aware = production["GMT MKT Interval"].to_pydatetime(tz=utc)
        for k in keys_to_remove:
            production.pop(k, None)

        production = {k: float(v) for k, v in production.items()}
        mapped_production = {MAPPING.get(k, k): v for k, v in production.items()}

        processed_data.append((dt_aware, mapped_production))
    return processed_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "US-SPP",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given zone."""

    if target_datetime is not None:
        current_year = datetime.now().year
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
        start = target_datetime - timedelta(days=1)
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
        dt = item[0].replace(tzinfo=utc)
        datapoint = {
            "zoneKey": zone_key,
            "datetime": dt,
            "production": item[1],
            "storage": {},
            "source": "spp.org",
        }
        data.append(datapoint)

    return data


def _NaN_safe_get(forecast: dict, key: str) -> Optional[float]:
    try:
        return float(forecast[key])
    except ValueError:
        return None


def fetch_load_forecast(
    zone_key: str = "US-SPP",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.now()

    if isinstance(target_datetime, datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    LOAD_URL = f"{US_PROXY}/chart-api/load-forecast/asFile?{HOST_PARAMETER}"

    raw_data = get_data(LOAD_URL)

    data = []
    for index in range(len(raw_data)):
        forecast = raw_data.loc[index].to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(tzinfo=utc)
        load = _NaN_safe_get(forecast, "STLF")
        if load is None:
            load = _NaN_safe_get(forecast, "MTLF")
        if load is None:
            logger.info(f"fetch_load_forecast: {dt} has no forecasted load")

        datapoint = {
            "datetime": dt,
            "value": load,
            "zoneKey": zone_key,
            "source": "spp.org",
        }

        data.append(datapoint)

    return data


@refetch_frequency(timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key: str = "US-SPP",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.now()

    if isinstance(target_datetime, datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)

    FORECAST_URL_PATH = (
        "%2F{0}%2F{1:02d}%2F{2:02d}%2FOP-MTRF-{0}{1:02d}{2:02d}0000.csv".format(
            dt.year, dt.month, dt.day
        )
    )
    FORECAST_URL = (
        f"{US_PROXY}/file-browser-api/download/midterm-resource-forecast?{HOST_PARAMETER}&path="
        + FORECAST_URL_PATH
    )

    raw_data = get_data(FORECAST_URL)

    # sometimes there is a leading whitespace in column names
    raw_data.columns = raw_data.columns.str.lstrip()

    data = []
    for index in range(len(raw_data)):
        forecast = raw_data.loc[index].to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(tzinfo=utc)

        # Get short term forecast if available, else medium term
        solar = _NaN_safe_get(forecast, "Solar Forecast MW")
        wind = _NaN_safe_get(forecast, "Wind Forecast MW")

        production = {}
        if solar is not None:
            production["solar"] = solar
        if wind is not None:
            production["wind"] = wind

        if production == {}:
            logger.info(
                f"fetch_wind_solar_forecasts: {dt} has no solar nor wind forecasted production"
            )
            continue

        datapoint = {
            "datetime": dt,
            "production": production,
            "zoneKey": zone_key,
            "source": "spp.org",
        }

        data.append(datapoint)

    return data


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production())
    print("fetch_load_forecast() -> ")
    print(fetch_load_forecast(target_datetime="20190125"))
    print("fetch_wind_solar_forecasts() -> ")
    print(fetch_wind_solar_forecasts(target_datetime="20190125"))
