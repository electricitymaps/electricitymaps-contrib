#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""


from datetime import datetime, timedelta
from io import StringIO
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
from dateutil import parser
from pytz import utc
from requests import Session

from parsers.lib.config import refetch_frequency
from parsers.lib.validation import validate_exchange

US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "host=https://marketplace.spp.org"

HISTORIC_GENERATION_BASE_URL = f"{US_PROXY}/file-browser-api/download/generation-mix-historical?{HOST_PARAMETER}&path="

GENERATION_URL = f"{US_PROXY}/chart-api/gen-mix/asFile?{HOST_PARAMETER}"

EXCHANGE_URL = f"{US_PROXY}/chart-api/interchange-trend/asFile?{HOST_PARAMETER}"
HISTORICAL_EXCHANGE_URL = (
    f"{US_PROXY}/file-browser-api/download/historical-tie-flow?{HOST_PARAMETER}&path="
)

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

EXCHANGE_MAPPING = {
    "AECI": "US-MIDW-AECI",
    "AMRN": "US-MIDW-MISO",
    "BLKW": "US-NW-PNM",
    "CLEC": "US-MIDW-MISO",
    "EDDY": "US-SW-EPE",
    "EES": "US-MIDW-MISO",
    "ERCOTE": "US-TEX-ERCO",
    "ERCOTN": "US-TEX-ERCO",
    "LAMAR": "US-NW-PSCO",
    "MEC": "US-MIDW-MISO",
    "SCSE": "US-NW-WACM",
    "SOUC": "US-SE-SOCO",
    "SPA": "US-CENT-SPA",
    "TVA": "US-TEN-TVA",
    "RCEAST": "US-NW-WAUW",
    "SPC": "CA-SK",
    "MCWEST": "US-NW-WAUW",
    "SGE": "US-NW-WACM",
    "ALTW": "US-MIDW-MISO",
    "DPC": "US-MIDW-MISO",
    "GRE": "US-MIDW-MISO",
    "MDU": "US-MIDW-MISO",
    "NSP": "US-MIDW-MISO",
    "OTP": "US-MIDW-MISO",
}
# NOTE
# Data sources return timestamps in GMT.
# Energy storage situation unclear as of 16/03/2018, likely to change quickly in future.


def get_data(url, session: Optional[Session] = None):
    """Returns a pandas dataframe."""

    s = session or Session()
    req = s.get(url)
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

        dt_aware = production["GMT MKT Interval"].to_pydatetime()
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

    try:
        raw_data = get_data(FORECAST_URL)
    except pd.errors.ParserError:
        logger.error(
            f"fetch_wind_solar_forecasts: {dt} has no forecast for url: {FORECAST_URL}"
        )
        return []

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


def fetch_live_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    data = get_data(EXCHANGE_URL, session)

    data = data.dropna(axis=0)
    data["GMTTime"] = pd.to_datetime(data["GMTTime"], utc=True)
    data = data.loc[data["GMTTime"] <= target_datetime]
    data = data.set_index("GMTTime")

    exchanges = format_exchange_data(
        data=data, zone_key1=zone_key1, zone_key2=zone_key2, logger=logger
    )
    return exchanges


def fetch_historical_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    filename = target_datetime.strftime("TieFlows_%b%Y.csv")
    file_url = f"{US_PROXY}/file-browser-api/download/historical-tie-flow?{HOST_PARAMETER}&path={filename}"

    data = get_data(file_url, session)

    data["GMTTIME"] = pd.to_datetime(data["GMTTIME"], utc=True)
    data = data.loc[
        (data["GMTTIME"] >= target_datetime - timedelta(days=1))
        & (data["GMTTIME"] <= target_datetime)
    ]
    data = data.set_index("GMTTIME")

    exchanges = format_exchange_data(
        data=data, zone_key1=zone_key1, zone_key2=zone_key2, logger=logger
    )
    return exchanges


def format_exchange_data(
    data: pd.DataFrame,
    zone_key1: str,
    zone_key2: str,
    logger: Logger = getLogger(__name__),
) -> list:
    """format exchanges data into list of data points"""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    data = data[[col for col in EXCHANGE_MAPPING]]
    data = data.melt(var_name="zone_key2", value_name="exchange", ignore_index=False)
    data.zone_key2 = data.zone_key2.map(EXCHANGE_MAPPING)

    data_filtered = data.loc[data["zone_key2"] == zone_key2]
    data_filtered = data_filtered.groupby([data_filtered.index])["exchange"].sum()

    all_data_points = []
    for dt in data_filtered.index:
        data_dt = data_filtered.loc[data_filtered.index == dt]
        data_point = {
            "sortedZoneKeys": sorted_zone_keys,
            "netFlow": round(data_dt.values[0], 4),
            "datetime": arrow.get(dt).datetime,
            "source": "spp.org",
        }
        all_data_points.append(data_point)
    validated_data_points = [x for x in all_data_points if validate_exchange(x, logger)]

    return validated_data_points


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    now = datetime.now(tz=utc)
    if (
        target_datetime is None
        or target_datetime > arrow.get(now).floor("day").datetime
    ):
        target_datetime = now
        exchanges = fetch_live_exchange(zone_key1, zone_key2, session, target_datetime)
    elif target_datetime < datetime(2014, 3, 1, tzinfo=utc):
        raise NotImplementedError(
            "Exchange data is not available from this sourc before 03/2014"
        )
    else:
        exchanges = fetch_historical_exchange(
            zone_key1, zone_key2, session, target_datetime
        )
    return exchanges


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production())
    print("fetch_exchange() -> ")
    print(fetch_exchange("US-CENT-SWPP", "US-MIDW-MISO"))
    print("fetch_load_forecast() -> ")
    print(fetch_load_forecast(target_datetime="20190125"))
    print("fetch_wind_solar_forecasts() -> ")
    print(fetch_wind_solar_forecasts(target_datetime="20221118"))
