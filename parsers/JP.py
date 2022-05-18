#!/usr/bin/env python3
# coding=utf-8
import datetime as dt
import logging

# The arrow library is used to handle datetimes
import arrow
import pandas as pd

from parsers import occtonet
from parsers.lib.config import refetch_frequency

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


@refetch_frequency(dt.timedelta(days=1))
def fetch_production(
    zone_key="JP-TK",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """
    Calculates production from consumption and imports for a given area
    All production is mapped to unknown
    """
    df = fetch_production_df(zone_key, session, target_datetime)
    # add a row to production for each entry in the dictionary:

    datalist = []

    for i in df.index:
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
            "source": "occtonet.or.jp, {}".format(sources[zone_key]),
        }
        datalist.append(data)

    return datalist


def fetch_production_df(
    zone_key="JP-TK",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
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
    zone_key="JP-TK", target_datetime=None, logger=logging.getLogger(__name__)
):
    """
    Returns the consumption for an area as a pandas DataFrame.
    For JP-CB the consumption file includes solar production.
    """
    if target_datetime is not None and zone_key in ZONES_ONLY_LIVE:
        raise NotImplementedError("This parser can only fetch live data")
    datestamp = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y%m%d")
    consumption_url = {
        "JP-HKD": "http://denkiyoho.hepco.co.jp/area/data/juyo_01_{}.csv".format(
            datestamp
        ),
        "JP-TH": "https://setsuden.nw.tohoku-epco.co.jp/common/demand/juyo_02_{}.csv".format(
            datestamp
        ),
        "JP-TK": "http://www.tepco.co.jp/forecast/html/images/juyo-d-j.csv",
        "JP-HR": "http://www.rikuden.co.jp/nw/denki-yoho/csv/juyo_05_{}.csv".format(
            datestamp
        ),
        "JP-CB": "https://powergrid.chuden.co.jp/denki_yoho_content_data/juyo_cepco003.csv",
        "JP-KN": "https://www.kansai-td.co.jp/yamasou/juyo1_kansai.csv",
        "JP-CG": "https://www.energia.co.jp/nw/jukyuu/sys/juyo_07_{}.csv".format(
            datestamp
        ),
        "JP-SK": "http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv",
        "JP-KY": "https://www.kyuden.co.jp/td_power_usages/csv/juyo-hourly-{}.csv".format(
            datestamp
        ),
        "JP-ON": "https://www.okiden.co.jp/denki2/juyo_10_{}.csv".format(datestamp),
    }

    # First roughly 40 rows of the consumption files have hourly data,
    # the parser skips to the rows with 5-min actual values
    if zone_key == "JP-KN":
        startrow = 57
    else:
        startrow = 54

    try:
        df = pd.read_csv(
            consumption_url[zone_key], skiprows=startrow, encoding="shift-jis"
        )
    except pd.errors.EmptyDataError as e:
        logger.exception("Data not available yet")
        raise e

    if zone_key in ["JP-TH"]:
        df.columns = ["Date", "Time", "cons", "solar", "wind"]
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


def fetch_consumption_forecast(
    zone_key="JP-KY",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Gets consumption forecast for specified zone."""
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime and zone_key == "JP-HKD":
        raise NotImplementedError("Past dates not yet implemented for selected region")
    datestamp = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y%m%d")
    # Forecasts ahead of current date are not available
    if datestamp > arrow.get().to("Asia/Tokyo").strftime("%Y%m%d"):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected region"
        )

    consumption_url = {
        "JP-HKD": "http://denkiyoho.hepco.co.jp/area/data/juyo_01_{}.csv".format(
            datestamp
        ),
        "JP-TH": "https://setsuden.nw.tohoku-epco.co.jp/common/demand/juyo_02_{}.csv".format(
            datestamp
        ),
        "JP-TK": "http://www.tepco.co.jp/forecast/html/images/juyo-j.csv",
        "JP-HR": "http://www.rikuden.co.jp/nw/denki-yoho/csv/juyo_05_{}.csv".format(
            datestamp
        ),
        "JP-CB": "https://powergrid.chuden.co.jp/denki_yoho_content_data/juyo_cepco003.csv",
        "JP-KN": "https://www.kansai-td.co.jp/yamasou/juyo1_kansai.csv",
        "JP-CG": "https://www.energia.co.jp/nw/jukyuu/sys/juyo_07_{}.csv".format(
            datestamp
        ),
        "JP-SK": "http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv",
        "JP-KY": "https://www.kyuden.co.jp/td_power_usages/csv/juyo-hourly-{}.csv".format(
            datestamp
        ),
        "JP-ON": "https://www.okiden.co.jp/denki2/juyo_10_{}.csv".format(datestamp),
    }
    # Skip non-tabular data at the start of source files
    if zone_key == "JP-KN":
        startrow = 16
    elif zone_key == "JP-TK":
        startrow = 7
    else:
        startrow = 13
    # Read the 24 hourly values
    df = pd.read_csv(
        consumption_url[zone_key], skiprows=startrow, nrows=24, encoding="shift-jis"
    )
    if zone_key == "JP-KN":
        df = df[["DATE", "TIME", "予想値(万kW)"]]
    else:
        try:
            df = df[["DATE", "TIME", "予測値(万kW)"]]
        except KeyError:
            df = df[["DATE", "TIME", "予測値（万kW)"]]
    df.columns = ["Date", "Time", "fcst"]

    df["datetime"] = df.apply(parse_dt, axis=1)

    # convert from 万kW to MW
    df["fcst"] = 10 * df["fcst"]
    # validate
    df = df.loc[df["fcst"] > 0]
    # return format
    data = []
    for i in df.index:
        data.append(
            {
                "zoneKey": zone_key,
                "datetime": df.loc[i, "datetime"].to_pydatetime(),
                "value": float(df.loc[i, "fcst"]),
                "source": sources[zone_key],
            }
        )

    return data


@refetch_frequency(dt.timedelta(days=1))
def fetch_price(
    zone_key="JP-TK",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if target_datetime is None:
        target_datetime = dt.datetime.now() + dt.timedelta(days=1)

    # price files contain data for fiscal year and not calendar year.
    if target_datetime.month <= 3:
        fiscal_year = target_datetime.year - 1
    else:
        fiscal_year = target_datetime.year
    url = "http://www.jepx.org/market/excel/spot_{}.csv".format(fiscal_year)
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

    start = target_datetime - dt.timedelta(days=1)
    df["Date"] = df["Date"].apply(lambda x: dt.datetime.strptime(x, "%Y/%m/%d"))
    df = df[(df["Date"] >= start.date()) & (df["Date"] <= target_datetime.date())]

    df["datetime"] = df.apply(
        lambda row: arrow.get(row["Date"])
        .shift(minutes=30 * (row["Period"] - 1))
        .replace(tzinfo="Asia/Tokyo"),
        axis=1,
    )

    data = list()
    for row in df.iterrows():
        data.append(
            {
                "zoneKey": zone_key,
                "currency": "JPY",
                "datetime": row[1]["datetime"].datetime,
                "price": round(
                    int(1000 * row[1][zone_key]), -1
                ),  # Convert from JPY/kWh to JPY/MWh
                "source": "jepx.org",
            }
        )

    return data


def parse_dt(row):
    """Parses timestamps from date and time."""
    if "AM" in row["Time"] or "PM" in row["Time"]:
        timestamp = (
            arrow.get(
                " ".join([row["Date"], row["Time"]]).replace("/", "-"),
                "YYYY-M-D H:mm A",
            )
            .replace(tzinfo="Asia/Tokyo")
            .datetime
        )
    else:
        timestamp = (
            arrow.get(
                " ".join([row["Date"], row["Time"]]).replace("/", "-"), "YYYY-M-D H:mm"
            )
            .replace(tzinfo="Asia/Tokyo")
            .datetime
        )
    return timestamp


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_price() ->")
    print(fetch_price())
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
