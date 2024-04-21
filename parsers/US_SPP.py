#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""

from datetime import datetime, timedelta, timezone
from io import StringIO
from logging import Logger, getLogger
from typing import Any

import pandas as pd
from dateutil import parser
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.validation import validate_exchange

SOURCE = "spp.org"
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
    "Other": "unknown",
    "Waste Heat": "unknown",
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


def get_data(url, session: Session | None = None):
    """Returns a pandas dataframe."""

    s = session or Session()
    req = s.get(url)
    df = pd.read_csv(StringIO(req.text))

    return df


def data_processor(df, logger: Logger) -> list[tuple[datetime, ProductionMix]]:
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
        logger.warning(
            f"New column '{heading}' present in US-SPP data source.",
            extra={"key": "US-SPP"},
        )

    processed_data = []
    for index in range(len(df)):
        mix = ProductionMix()
        production = df.loc[index].to_dict()
        dt_aware = production["GMT MKT Interval"].to_pydatetime()
        for k in keys_to_remove | unknown_keys:
            production.pop(k, None)

        for k, v in production.items():
            mix.add_value(MAPPING[k], float(v))
        processed_data.append((dt_aware, mix))
    return processed_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
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

    production_list = ProductionBreakdownList(logger)
    for dt, mix in processed_data:
        production_list.append(
            zoneKey=zone_key,
            datetime=dt.replace(tzinfo=timezone.utc),
            production=mix,
            source=SOURCE,
        )

    return production_list.to_list()


def _NaN_safe_get(forecast: dict, key: str) -> float | None:
    try:
        return float(forecast[key])
    except ValueError:
        return None


def fetch_load_forecast(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.now()

    if isinstance(target_datetime, datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    LOAD_URL = f"{US_PROXY}/chart-api/load-forecast/asFile?{HOST_PARAMETER}"

    raw_data = get_data(LOAD_URL)

    consumption_list = TotalConsumptionList(logger)
    for index in range(len(raw_data)):
        forecast = raw_data.loc[index].to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(tzinfo=timezone.utc)
        load = _NaN_safe_get(forecast, "STLF")
        if load is None:
            load = _NaN_safe_get(forecast, "MTLF")
        if load is None:
            logger.info(f"fetch_load_forecast: {dt} has no forecasted load")

        consumption_list.append(
            datetime=dt,
            consumption=load,
            zoneKey=zone_key,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return consumption_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the load forecast (in MW) of a given zone."""

    if not target_datetime:
        target_datetime = datetime.now()

    if isinstance(target_datetime, datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)

    FORECAST_URL_PATH = f"%2F{dt.year}%2F{dt.month:02d}%2F{dt.day:02d}%2FOP-MTRF-{dt.year}{dt.month:02d}{dt.day:02d}0000.csv"
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

    production_list = ProductionBreakdownList(logger)
    for index in range(len(raw_data)):
        forecast = raw_data.loc[index].to_dict()

        dt = parser.parse(forecast["GMTIntervalEnd"]).replace(tzinfo=timezone.utc)

        # Get short term forecast if available, else medium term
        solar = _NaN_safe_get(forecast, "Solar Forecast MW")
        wind = _NaN_safe_get(forecast, "Wind Forecast MW")

        if solar is None and wind is None:
            logger.info(
                f"fetch_wind_solar_forecasts: {dt} has no solar nor wind forecasted production"
            )
            continue

        mix = ProductionMix(solar=solar, wind=wind)

        production_list.append(
            datetime=dt,
            production=mix,
            zoneKey=zone_key,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return production_list.to_list()


def fetch_live_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
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
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        return []
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
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    logger: Logger = getLogger(__name__),
) -> list:
    """format exchanges data into list of data points"""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    data = data[list(EXCHANGE_MAPPING)]
    data = data.melt(var_name="zone_key2", value_name="exchange", ignore_index=False)
    data.zone_key2 = data.zone_key2.map(EXCHANGE_MAPPING)

    data_filtered = data.loc[data["zone_key2"] == zone_key2]
    data_filtered = data_filtered.groupby([data_filtered.index])["exchange"].sum()

    exchange_list = ExchangeList(logger)
    for dt in data_filtered.index:
        data_dt = data_filtered.loc[data_filtered.index == dt]
        exchange_list.append(
            zoneKey=sorted_zone_keys,
            netFlow=round(data_dt.values[0], 4),
            datetime=dt.to_pydatetime(),
            source=SOURCE,
        )

    return [x for x in exchange_list.to_list() if validate_exchange(x, logger)]


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    now = datetime.now(tz=timezone.utc)
    if target_datetime is None or target_datetime > now.date():
        target_datetime = now
        exchanges = fetch_live_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )
    elif target_datetime < datetime(2014, 3, 1, tzinfo=timezone.utc):
        raise NotImplementedError(
            "Exchange data is not available from this source before 03/2014"
        )
    else:
        exchanges = fetch_historical_exchange(
            zone_key1, zone_key2, session, target_datetime, logger
        )
    return exchanges


if __name__ == "__main__":
    print("fetch_production() -> ")
    print(fetch_production(zone_key=ZoneKey("US-SW-AZPS")))
    print("fetch_exchange() -> ")
    print(fetch_exchange("US-CENT-SWPP", "US-MIDW-MISO"))
    print("fetch_load_forecast() -> ")
    print(
        fetch_load_forecast(zone_key=ZoneKey("US-SW-AZPS"), target_datetime="20190125")
    )
    print("fetch_wind_solar_forecasts() -> ")
    print(
        fetch_wind_solar_forecasts(
            zone_key=ZoneKey("US-SW-AZPS"), target_datetime="20221118"
        )
    )
