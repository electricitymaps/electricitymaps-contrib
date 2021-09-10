#!/usr/bin/env python3
# coding=utf-8
import datetime
from io import StringIO
import logging
from typing import Dict, List, Union

import arrow
import pandas as pd
import requests


# Abbreviations:
# JP-HKD : Hokkaido
# JP-TH  : Tohoku (incl. Niigata)
# JP-TK  : Tokyo area (Kanto)
# JP-CB  : Chubu
# JP-HR  : Hokuriku
# JP-KN  : Kansai
# JP-CG  : Chugoku
# JP-SK  : Shikoku
# JP-KY  : Kyushu
# JP-ON  : Okinawa

# In selector, they correspond to (format: Japanese original name [english translation])
exchange_mapping = {
    "JP-HKD->JP-TH": [
        1
    ],  # 北海道・本州間電力連系設備 [Hokkaido-Honshu Electric Power Interconnection Facility]
    "JP-TH->JP-TK": [2],  # 相馬双葉幹線 [Soma Futaba Trunk Line]
    "JP-CB->JP-TK": [3],  # 周波数変換設備 [Frequency conversion equipment]
    "JP-CB->JP-KN": [4],  # 三重東近江線 [Mie Higashi-Omi Line]
    "JP-CB->JP-HR": [
        5,
        11,
    ],  # 南福光連系所・南福光変電所の連系設備 [Minami-Fukumitsu Interconnection / Minami-Fukumitsu Substation Interconnection equipment] and 北陸フェンス [Hokuriku fence]
    "JP-HR->JP-KN": [6],  # 越前嶺南線 [Echizen Rinan Line]
    "JP-CG->JP-KN": [
        7
    ],  # 西播東岡山線・山崎智頭線 [Nishiban Higashi Okayama Line / Yamazaki Chitou Line]
    "JP-KN->JP-SK": [8],  # 阿南紀北直流幹線 [Anan Kihoku DC Trunk Line]
    "JP-CG->JP-SK": [9],  # 本四連系線 [This Quadruple Interconnection Line]
    "JP-CG->JP-KY": [10],  # 関門連系線 [Kanmon Interconnection Line]
}

SOURCE_URL = "occtonet.occto.or.jp"
EXCHANGE_COLUMNS = ["sortedZoneKeys", "netFlow", "source"]


def fetch_exchange(
    zone_key1="JP-TH",
    zone_key2="JP-TK",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two zones."""
    if not session:
            session = requests.session()
    
    query_date = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y/%m/%d")

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    exch_id = exchange_mapping[sortedZoneKeys]
    
    cookies = get_cookies(session)

    df = pd.DataFrame()
    for i in range(len(exch_id)):
        # TODO reformat that piece of code
        Headers = get_headers(session, exch_id[i], query_date)
        # Query data
        Headers = get_request_token(session, Headers)
        _df = get_exchange(session, Headers)
        if df.empty:
            df = _df
        else:
            df += _df
            df.reset_index()

    # TODO determine if this is needed
    # fix occurrences of 24:00hrs
    list24 = list(df[(df.index.hour == 24) & (df.index.minute == 0)].index)
    for idx in list24:
        df.loc[idx, "Date"] = (
            arrow.get(df.loc[idx, "Date"]).shift(days=1).strftime("%Y/%m/%d")
        )
        df.loc[idx, "Time"] = "00:00"

    # correct flow direction, if needed
    flows_to_revert = ["JP-CB->JP-TK", "JP-CG->JP-KN", "JP-CG->JP-SK"]
    if sortedZoneKeys in flows_to_revert:
        df["netFlow"] = -1 * df["netFlow"]

    df["source"] = SOURCE_URL

    df["sortedZoneKeys"] = sortedZoneKeys
    df = df[EXCHANGE_COLUMNS]
    df = df.reset_index()

    results = df.to_dict("records")
    return results


def fetch_exchange_forecast(
    zone_key1="JP-TH",
    zone_key2="JP-TK",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Gets exchange forecast between two specified zones."""
    # TODO align implementation with fetch_exchange
    if not session:
        session = requests.session()

    # get target date in time zone Asia/Tokyo
    query_date = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y/%m/%d")
    # Forecasts ahead of current date are not available
    if query_date > arrow.get().to("Asia/Tokyo").strftime("%Y/%m/%d"):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected exchange"
        )

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    exch_id = exchange_mapping[sortedZoneKeys]

    cookies = get_cookies(session)

    df = pd.DataFrame()
    for i in range(len(exch_id)):
        # 
        Headers = get_headers(session, exch_id[i], query_date)
        # Query data
        Headers = get_request_token(session, Headers)
        _df = get_exchange_fcst(session, Headers)
        if df.empty:
            df = _df
        else:
            _df.set_index(["Date", "Time"])
            df += _df
            df.reset_index()

    # TODO is this needed ?
    # fix possible occurrences of 24:00hrs
    list24 = list(df.index[df["Time"] == "24:00"])
    for idx in list24:
        df.loc[idx, "Date"] = (
            arrow.get(str(df.loc[idx, "Date"])).shift(days=1).strftime("%Y/%m/%d")
        )
        df.loc[idx, "Time"] = "00:00"

    # correct flow direction, if needed
    flows_to_revert = ["JP-CB->JP-TK", "JP-CG->JP-KN", "JP-CG->JP-SK"]
    if sortedZoneKeys in flows_to_revert:
        df["netFlow"] = -1 * df["netFlow"]

    # Add zonekey, source
    df["source"] = SOURCE_URL
    df["sortedZoneKeys"] = sortedZoneKeys
    df = df[EXCHANGE_COLUMNS]
    df = df.reset_index()

    # Format output
    results = df.to_dict("records")
    return results

def get_cookies(
    session: Union[requests.Session, None] = None
) -> requests.cookies.RequestsCookieJar:
    if not session:
        session = requests.session()
    session.get("http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login")
    return session.cookies


def get_headers(
    session: requests.Session,
    exch_id: int,
    date: str,
):
    form_data = {
        "ajaxToken": "",
        "downloadKey": "",
        "fwExtention.actionSubType": "headerInput",
        "fwExtention.actionType": "reference",
        "fwExtention.formId": "CA01S070P",
        "fwExtention.jsonString": "",
        "fwExtention.pagingTargetTable": "",
        "fwExtention.pathInfo": "CA01S070C",
        "fwExtention.prgbrh": "0",
        "msgArea": "・マージンには需給調整市場の連系線確保量が含まれております。",
        "requestToken": "",
        "requestTokenBk": "",
        "searchReqHdn": "",
        "simFlgHdn": "",
        "sntkTgtRklCdHdn": "",
        "spcDay": date,
        "spcDayHdn": "",
        "tgtRkl": "{:02d}".format(exch_id),
        "tgtRklHdn": "01,北海道・本州間電力連系設備,02,相馬双葉幹線,03,周波数変換設備,04,三重東近江線,05,南福光連系所・南福光変電所の連系設備,06,越前嶺南線,07,西播東岡山線・山崎智頭線,08,阿南紀北直流幹線,09,本四連系線,10,関門連系線,11,北陸フェンス",
        "transitionContextKey": "DEFAULT",
        "updDaytime": "",
    }

    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    headers = r.text
    headers = eval(headers.replace("false", "False").replace("null", "None"))
    if headers["root"]["errMessage"]:
        raise RuntimeError(
            "Headers not available due to {}".format(headers["root"]["errMessage"])
        )
    else:
        form_data["msgArea"] = headers["root"]["bizRoot"]["header"]["msgArea"]["value"]
        form_data["searchReqHdn"] = headers["root"]["bizRoot"]["header"]["searchReqHdn"][
            "value"
        ]
        form_data["spcDayHdn"] = headers["root"]["bizRoot"]["header"]["spcDayHdn"][
            "value"
        ]
        form_data["updDaytime"] = headers["root"]["bizRoot"]["header"]["updDaytime"][
            "value"
        ]
    return form_data


def get_request_token(
    session: requests.Session,
    form_data: Dict[str, str],
):
    form_data["fwExtention.actionSubType"] = "ok"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    headers = r.text
    headers = eval(headers.replace("false", "False").replace("null", "None"))
    if headers["root"]["errFields"]:
        raise RuntimeError(
            "Request token not available due to {}".format(headers["root"]["errFields"])
        )
    else:
        form_data["downloadKey"] = headers["root"]["bizRoot"]["header"]["downloadKey"][
            "value"
        ]
        form_data["requestToken"] = headers["root"]["bizRoot"]["header"]["requestToken"][
            "value"
        ]
    return form_data


def _get_exchange(session: requests.Session, form_data: Dict[str, str], columns: List[str]):
    def parse_dt(str_dt: str) -> datetime:
        return arrow.get(str_dt).replace(tzinfo="Asia/Tokyo").datetime
    form_data["fwExtention.actionSubType"] = "download"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    r.encoding = "shift-jis"
    df = pd.read_csv(StringIO(r.text), delimiter=",")
    df = df[columns]
    df.columns = ["date", "time", "netFlow"]
    df.loc[:, "datetime"] = (df.date + " " + df.time).apply(lambda x: parse_dt(x))
    df = df.set_index("datetime")
    df = df.drop(columns=["date", "time"])
    df = df.dropna()
    return df

def get_exchange(session, form_data):
    return _get_exchange(session, form_data, ["対象日付", "対象時刻", "潮流実績"])


def get_exchange_fcst(session, form_data):
    return _get_exchange(session, form_data, ["対象日付", "対象時刻", "計画潮流(順方向)"])


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_exchange(JP-CB, JP-HR) ->")
    print(fetch_exchange("JP-CB", "JP-HR")[-3:])
    print("fetch_exchange(JP-CG, JP-KY) ->")
    print(fetch_exchange("JP-CG", "JP-KY")[-3:])
    print("fetch_exchange_forecast(JP-CB, JP-HR) ->")
    print(fetch_exchange_forecast("JP-CB", "JP-HR")[-3:])
    print("fetch_exchange_forecast(JP-CG, JP-KY) ->")
    print(fetch_exchange_forecast("JP-CG", "JP-KY")[-3:])
