#!/usr/bin/env python3
from datetime import datetime, timedelta
from io import BytesIO, StringIO
from logging import Logger, getLogger
from typing import Any
from zipfile import ZipFile
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.config import ZONES_CONFIG
from electricitymap.contrib.lib.models.event_lists import (
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers import occtonet
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

# Abbreviations
# JP-HKD : Hokkaido
# JP-TH  : Tohoku
# JP-TK  : Tokyo area
# JP-CB  : Chubu
# JP-HR  : Hokuriku
# JP-KN  : Kansai
# JP-SK  : Shikoku
# JP-KY  : Kyushu
# JP-ON  : Okinawa
# JP-CG  : Chūgoku

sources = {
    "JP-HKD": "denkiyoho.hepco.co.jp",
    "JP-TH": "setsuden.nw.tohoku-epco.co.jp",
    "JP-TK": "www.tepco.co.jp",
    "JP-CB": "denki-yoho.chuden.jp",
    "JP-HR": "www.rikuden.co.jp/denki-yoho",
    "JP-KN": "www.kepco.co.jp",
    "JP-SK": "www.yonden.co.jp",
    "JP-CG": "www.energia.co.jp",
    "JP-KY": "www.kyuden.co.jp/power_usages/pc.html",
    "JP-ON": "www.okiden.co.jp/denki/",
}
ZONES_ONLY_LIVE = ["JP-TK", "JP-CB", "JP-SK"]
ZONE_INFO = ZoneInfo("Asia/Tokyo")


def get_wind_capacity(datetime: datetime, zone_key, logger: Logger):
    ZONE_CONFIG = ZONES_CONFIG[zone_key]
    try:
        capacity = ZONE_CONFIG["capacity"]["wind"]
        if zone_key == "JP-HKD":
            if datetime.year <= 2019:
                capacity = 480
            elif datetime.year == 2020:
                capacity = 520
            elif datetime.year >= 2021:
                capacity = 577
    except Exception as e:
        logger.error(f"Wind capacity not found in configuration file: {e.args}")
        capacity = None
    return capacity


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Calculates production from consumption and imports for a given area
    All production is mapped to unknown
    """
    df = fetch_production_df(zone_key, session, target_datetime)
    # add a row to production for each entry in the dictionary:

    datalist = []

    for i in df.index:
        capacity = get_wind_capacity(
            df.loc[i, "datetime"].to_pydatetime(), zone_key, logger
        )
        data = {
            "zoneKey": zone_key,
            "datetime": df.loc[i, "datetime"].to_pydatetime(),
            "production": {
                "biomass": None,
                "coal": None,
                "gas": None,
                "hydro": None,
                "nuclear": None,
                "oil": None,
                "solar": df.loc[i, "solar"] if "solar" in df.columns else None,
                "wind": None,
                "geothermal": None,
                "unknown": df.loc[i, "unknown"],
            },
            "capacity": {"wind": capacity if capacity is not None else {}},
            "source": f"occto.or.jp, {sources[zone_key]}",
        }
        datalist.append(data)
    return datalist


def fetch_production_df(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Calculates production from consumption and imports for a given area.
    All production is mapped to unknown.
    """
    exch_map = {
        "JP-HKD": ["JP-TH"],
        "JP-TH": ["JP-TK", "JP-HKD"],
        "JP-TK": ["JP-TH", "JP-CB"],
        "JP-CB": ["JP-TK", "JP-HR", "JP-KN"],
        "JP-HR": ["JP-CB", "JP-KN"],
        "JP-KN": ["JP-CB", "JP-HR", "JP-SK", "JP-CG"],
        "JP-SK": ["JP-KN", "JP-CG"],
        "JP-CG": ["JP-KN", "JP-SK", "JP-KY"],
        "JP-ON": [],
        "JP-KY": ["JP-CG"],
    }
    df = fetch_consumption_df(zone_key, target_datetime)
    df["imports"] = 0
    for zone in exch_map[zone_key]:
        df2 = occtonet.fetch_exchange(
            zone_key1=zone_key,
            zone_key2=zone,
            session=session,
            target_datetime=target_datetime,
        )
        df2 = pd.DataFrame(df2)
        exchname = df2.loc[0, "sortedZoneKeys"]
        df2 = df2[["datetime", "netFlow"]]
        df2.columns = ["datetime", exchname]
        df = pd.merge(df, df2, how="inner", on="datetime")
        if exchname.split("->")[-1] == zone_key:
            df["imports"] = df["imports"] + df[exchname]
        else:
            df["imports"] = df["imports"] - df[exchname]
    # By default all production is mapped to unknown
    df["unknown"] = df["cons"] - df["imports"]
    # When there is solar, remove it from other production
    if "solar" in df.columns:
        df["unknown"] = df["unknown"] - df["solar"]
    return df


def fetch_consumption_df(
    zone_key: str = "JP-TK",
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    """
    Returns the consumption for an area as a pandas DataFrame.
    For JP-CB the consumption file includes solar production.
    """
    if target_datetime is not None and zone_key in ZONES_ONLY_LIVE:
        raise NotImplementedError("This parser can only fetch live data")
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")
    consumption_url = {
        "JP-HKD": f"http://denkiyoho.hepco.co.jp/area/data/juyo_01_{datestamp}.csv",
        "JP-TH": f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/juyo_02_{datestamp}.csv",
        "JP-TK": "https://www.tepco.co.jp/forecast/html/images/juyo-d1-j.csv",
        "JP-HR": f"http://www.rikuden.co.jp/nw/denki-yoho/csv/juyo_05_{datestamp}.csv",
        "JP-CB": "https://powergrid.chuden.co.jp/denki_yoho_content_data/juyo_cepco003.csv",
        "JP-KN": "https://www.kansai-td.co.jp/yamasou/juyo1_kansai.csv",
        "JP-CG": f"https://www.energia.co.jp/nw/jukyuu/sys/juyo_07_{datestamp}.csv",
        "JP-SK": "http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv",
        "JP-KY": f"https://www.kyuden.co.jp/td_power_usages/csv/juyo-hourly-{datestamp}.csv",
        "JP-ON": f"https://www.okiden.co.jp/denki2/juyo_10_{datestamp}.csv",
    }

    # First roughly 40 rows of the consumption files have hourly data,
    # the parser skips to the rows with 5-min actual values
    startrow = 57 if zone_key == "JP-KN" else 54

    try:
        df = pd.read_csv(
            consumption_url[zone_key], skiprows=startrow, encoding="shift-jis"
        )
    except pd.errors.EmptyDataError as e:
        logger.exception("Data not available yet")
        raise e

    if zone_key in ["JP-TH"]:
        df.columns = ["Date", "Time", "cons", "solar", "wind"]
    elif zone_key in ["JP-TK"]:
        df.columns = ["Date", "Time", "cons", "solar", "solar_pct"]
    else:
        df.columns = ["Date", "Time", "cons", "solar"]
    # Convert 万kW to MW
    df["cons"] = 10 * df["cons"]
    if "solar" in df.columns:
        df["solar"] = 10 * df["solar"]

    df = df.dropna()
    df["datetime"] = df.apply(parse_dt, axis=1)
    if "solar" in df.columns:
        df = df[["datetime", "cons", "solar"]]
    else:
        df = df[["datetime", "cons"]]
    return df


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO) + timedelta(days=1)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    # price files contain data for fiscal year and not calendar year.
    if target_datetime.month <= 3:
        fiscal_year = target_datetime.year - 1
    else:
        fiscal_year = target_datetime.year
    url = f"http://www.jepx.jp/market/excel/spot_{fiscal_year}.csv"
    df = pd.read_csv(url, encoding="shift-jis")

    df = df.iloc[:, [0, 1, 6, 7, 8, 9, 10, 11, 12, 13, 14]]
    df.columns = [
        "Date",
        "Period",
        "JP-HKD",
        "JP-TH",
        "JP-TK",
        "JP-CB",
        "JP-HR",
        "JP-KN",
        "JP-CG",
        "JP-SK",
        "JP-KY",
    ]

    if zone_key not in df.columns[2:]:
        return []

    start = target_datetime - timedelta(days=1)
    df["Date"] = pd.to_datetime(df["Date"], format="%Y/%m/%d").dt.date
    df = df[(df["Date"] >= start.date()) & (df["Date"] <= target_datetime.date())]

    df["datetime"] = df.apply(
        lambda row: datetime.combine(row["Date"], datetime.min.time()).replace(
            tzinfo=ZONE_INFO
        )
        + timedelta(minutes=30 * (row["Period"] - 1)),
        axis=1,
    )

    data = []
    for row in df.iterrows():
        data.append(
            {
                "zoneKey": zone_key,
                "currency": "JPY",
                "datetime": row[1]["datetime"].to_pydatetime(),
                "price": round(
                    int(1000 * row[1][zone_key]), -1
                ),  # Convert from JPY/kWh to JPY/MWh
                "source": "jepx.jp",
            }
        )

    return data


def parse_dt(row):
    """Parses datetime objects from date and time strings."""
    format_string = "%Y/%m/%d %H:%M"
    if "AM" in row["Time"] or "PM" in row["Time"]:
        format_string = "%Y/%m/%d %I:%M %p"
    datetime_string = " ".join([row["Date"], row["Time"]])
    return datetime.strptime(datetime_string, format_string).replace(tzinfo=ZONE_INFO)


SOURCES_FORECAST_DATA = {
    "JP-HKD": "denkiyoho.hepco.co.jp",
    "JP-TH": "setsuden.nw.tohoku-epco.co.jp",
    "JP-TK": "www.tepco.co.jp/forecast",
    "JP-CB": "powergrid.chuden.co.jp",
    "JP-HR": "www.rikuden.co.jp/nw/denki-yoho",
    "JP-KN": "www.kansai-td.co.jp",
    "JP-SK": "www.yonden.co.jp",
    "JP-CG": "www.energia.co.jp",
    "JP-KY": "www.kyuden.co.jp",
    "JP-ON": "www.okiden.co.jp/denki2/",
}


def read_csv_forecast(
    datestamp, zone_key, session, logger, data_type=None
):  # data_type = generation_fcst or consumption_fcst
    """Reads the file where the forecast data is given, for a given zone in Japan. Now implemented for consumption and generation forecast data."""
    if datestamp < datetime.now(ZONE_INFO).strftime("%Y%m%d"):
        raise NotImplementedError("Past dates not implemented for selected region")

    # Forecasts ahead of current date are not available for JP-KY
    if datestamp > datetime.now(ZONE_INFO).strftime("%Y%m%d") and zone_key == "JP-KY":
        raise NotImplementedError(
            "Future dates (local time) not implemented for selected region"
        )

    # Forecasts ahead of tomorrow's date are not available
    if datestamp > (datetime.now(ZONE_INFO) + timedelta(days=1)).strftime("%Y%m%d"):
        raise NotImplementedError(
            "Dates after tomorrow (local time) not implemented for selected region"
        )

    # Urls for some Japan zones based on datestamp
    forecast_url = {
        "JP-HKD": f"http://denkiyoho.hepco.co.jp/area/data/{datestamp}_hokkaido_yosoku.csv",
        "JP-HR": f"https://www.rikuden.co.jp/nw/denki-yoho/csv/yosoku_05_{datestamp}.csv",
        "JP-KN": f"https://www.kansai-td.co.jp/interchange/denkiyoho/imbalance/{datestamp}_yosoku.csv",
        "JP-CG": f"https://www.energia.co.jp/nw/jukyuu/sys/{datestamp[:6]}_jyukyu2_chugoku.zip",
        "JP-KY": rf"https://www.kyuden.co.jp/td_power_usages/csv/kouhyo/imbalance/21110_TSO9_0_{datestamp}.csv?a={datestamp}\d{6}",
        "JP-ON": f"http://www.okiden.co.jp/denki2/dem_pg/csv/jukyu_yosoku_{datestamp}.csv",
    }

    # For zones with different URLs for today vs tomorrow
    if datestamp == datetime.now(ZONE_INFO).strftime("%Y%m%d"):
        forecast_url["JP-TH"] = (
            f"https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_{datestamp}.csv"
        )
        forecast_url["JP-TK"] = (
            "https://www4.tepco.co.jp/forecast/html/images/AREA_YOSOKU.csv"
        )
        forecast_url["JP-CB"] = (
            "https://powergrid.chuden.co.jp/denki_yoho_content_data/keito_yosoku_cepco003.csv"
        )
        forecast_url["JP-SK"] = (
            "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_today.csv"
        )
    # TODO: what time the new doc is created for next day?
    elif datestamp == (datetime.now(ZONE_INFO) + timedelta(days=1)).strftime("%Y%m%d"):
        forecast_url["JP-TH"] = (
            "https://setsuden.nw.tohoku-epco.co.jp/common/demand/area_tso_yosoku_y.csv"
        )
        forecast_url["JP-TK"] = (
            "https://www4.tepco.co.jp/forecast/html/images/AREA_ONCE_YOSOKU.csv"
        )
        forecast_url["JP-SK"] = (
            "https://www.yonden.co.jp/nw/denkiyoho/supply_demand/csv/yosoku_tomorrow.csv"
        )
        if zone_key == "JP-CB":  # Raise exception for JP-CB
            raise ValueError(
                f"Forecast data for tomorrow not available for zone: {zone_key}"
            )

    # Skip non-tabular data at the start of source files
    startrow = 1 if zone_key == "JP-HR" else 3 if zone_key == "JP-KN" else 2

    # Get response from correspondent url
    response = session.get(forecast_url[zone_key])

    # Parse the different formats
    df = pd.DataFrame()
    if zone_key == "JP-CG":
        with ZipFile(BytesIO(response.content)) as z:
            target_file = f"{datestamp}_yosoku_chugoku.csv"
            if target_file in z.namelist():
                with z.open(target_file) as f:
                    df = pd.read_csv(f, encoding="shift_jis", skiprows=startrow)
            else:
                logger.error(f"File '{target_file}' not found in the zip archive.")
                logger.debug(f"Available files: {z.namelist()}")
    else:
        content = response.content.decode("shift_jis")
        df = pd.read_csv(StringIO(content), skiprows=startrow)

    # Check if df is still empty after the above operations
    if df.empty:
        logger.error(f"Failed to load forecast data for {zone_key}")
        raise ValueError(f"Could not obtain forecast data for zone: {zone_key}")

    # Consumption or generation data
    if data_type == "consumption_fcst":
        column_name_japanese = "エリア総需要量"
    elif data_type == "generation_fcst":
        column_name_japanese = "エリア総発電量"

    # Extract the correspondant information from the files for each zone
    if zone_key == "JP-HKD" or zone_key == "JP-HR":
        df = df[["日付", "時間帯_自", column_name_japanese + "(kWh)"]]
    elif zone_key == "JP-KN" or zone_key == "JP-KY":
        if zone_key == "JP-KY":
            df = df.drop(index=0)
        df = df[["日付", "時間帯＿自", column_name_japanese]]
    elif zone_key == "JP-CG" or zone_key == "JP-CB" or zone_key == "JP-SK":
        df = df[["日付", "時間帯_自", column_name_japanese]]
    elif zone_key == "JP-ON" or zone_key == "JP-TH":
        df = df[["DATE", "時間帯_自", column_name_japanese + "(kWh)"]]
    elif zone_key == "JP-TK":
        df = df[
            ["日付(yyyymmdd)", "時間帯_自(HH:MI)", column_name_japanese + "[30分kWh]"]
        ]

    df.columns = ["Date", "Time", data_type]

    return df


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZoneKey("JP-HKD"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets demand/consumption forecast for every half hour for the specified Japan zones in MW."""
    # Session
    session = session or Session()

    # Date
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")

    # Read csv
    df = read_csv_forecast(
        datestamp, zone_key, session, logger, data_type="consumption_fcst"
    )

    # Transform to MW: the data is given every half hour
    df["consumption_fcst"] = df["consumption_fcst"].astype(float) * 2 / 1000

    all_consumption_events = df  # all events with a datetime and a consumption value
    consumption_list = TotalConsumptionList(logger)

    for row in all_consumption_events.itertuples():
        if (
            zone_key == "JP-HR"
            or zone_key == "JP-ON"
            or zone_key == "JP-TH"
            or zone_key == "JP-CB"
        ):
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y/%m/%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-TK":
            # Format as string in the format "YYYYMMDD HHMM" and parse
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time:04d}", "%Y%m%d %H%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-KY":
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        else:
            # Use strptime to directly parse the date integer and time string
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)

        consumption_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            consumption=row.consumption_fcst,
            source=SOURCES_FORECAST_DATA[zone_key],
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


def fetch_generation_forecast(
    zone_key: ZoneKey = ZoneKey("JP-HKD"),  # Just as default
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets generation forecast for every half hour for the specified Japan zones in MW."""

    # Session
    session = session or Session()

    # Date
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)

    datestamp = target_datetime.astimezone(ZONE_INFO).strftime("%Y%m%d")

    # Read csv
    df = read_csv_forecast(
        datestamp, zone_key, session, logger, data_type="generation_fcst"
    )

    # Transform to MW: the data is given every half hour
    df["generation_fcst"] = df["generation_fcst"].astype(float) * 2 / 1000

    all_generation_events = df  # all events with a datetime and a generation value
    generation_list = TotalProductionList(logger)

    for row in all_generation_events.itertuples():
        if (
            zone_key == "JP-HR"
            or zone_key == "JP-ON"
            or zone_key == "JP-TH"
            or zone_key == "JP-CB"
        ):
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y/%m/%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-TK":
            # Format as string in the format "YYYYMMDD HHMM" and parse
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time:04d}", "%Y%m%d %H%M"
            ).replace(tzinfo=ZONE_INFO)
        elif zone_key == "JP-KY":
            event_datetime = datetime.strptime(
                f"{row.Date} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)
        else:
            # Use strptime to directly parse the date integer and time string
            event_datetime = datetime.strptime(
                f"{row.Date:08d} {row.Time}", "%Y%m%d %H:%M"
            ).replace(tzinfo=ZONE_INFO)

        generation_list.append(
            zoneKey=zone_key,
            datetime=event_datetime,
            value=row.generation_fcst,
            source=SOURCES_FORECAST_DATA[zone_key],
            sourceType=EventSourceType.forecasted,
        )
    return generation_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    """
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
    """
    print("fetch_consumption_forecast() ->")
    print(fetch_consumption_forecast())
    print("fetch_consumption_forecast(JP-TH) ->")
    print(fetch_consumption_forecast("JP-TH"))
    print("fetch_consumption_forecast(JP-TK) ->")
    print(fetch_consumption_forecast("JP-TK"))
    print("fetch_consumption_forecast(JP-CB) ->")
    print(fetch_consumption_forecast("JP-CB"))
    print("fetch_consumption_forecast(JP-KN) ->")
    print(fetch_consumption_forecast("JP-KN"))
    print("fetch_consumption_forecast(JP-SK) ->")
    print(fetch_consumption_forecast("JP-SK"))
    print("fetch_consumption_forecast(JP-KY) ->")
    print(fetch_consumption_forecast("JP-KY"))
    print("fetch_consumption_forecast(JP-ON) ->")
    print(fetch_consumption_forecast("JP-ON"))

    print(
        fetch_generation_forecast(
            zone_key="JP-HKD", target_datetime=datetime(2025, 4, 25)
        )
    )

    print(
        fetch_consumption_forecast(
            zone_key="JP-HKD", target_datetime=datetime(2025, 4, 25)
        )
    )
