#!/usr/bin/env python3
from datetime import datetime
from io import StringIO
from logging import Logger, getLogger

import arrow
import pandas as pd
from requests import Session, cookies

from .lib.exceptions import ParserException

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
EXCHANGE_MAPPING = {
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
# correct flow direction, if needed
FLOWS_TO_REVERT = ["JP-CB->JP-TK", "JP-CG->JP-KN", "JP-CG->JP-SK"]

SOURCE_URL = "occtonet.occto.or.jp"
EXCHANGE_COLUMNS = ["sortedZoneKeys", "netFlow", "source"]


def _fetch_exchange(
    session: Session, datetime: datetime, sorted_zone_keys: str
) -> list[dict]:
    exch_id = EXCHANGE_MAPPING[sorted_zone_keys]

    # This authorises subsequent calls
    _cookies = get_cookies(session)

    df = pd.DataFrame()
    for i in range(len(exch_id)):
        form_data = get_form_data(session, exch_id[i], datetime)
        _df = get_exchange(session, form_data)
        if df.empty:
            df = _df
        else:
            df += _df
            df.reset_index()

    if sorted_zone_keys in FLOWS_TO_REVERT:
        df["netFlow"] = -1 * df["netFlow"]

    df["source"] = SOURCE_URL

    df["sortedZoneKeys"] = sorted_zone_keys
    df = df[EXCHANGE_COLUMNS]
    df = df.reset_index()

    results = df.to_dict("records")
    # For some reason, to_dict converts datetimes to Timestamps
    # See https://stackoverflow.com/questions/64171427/pandas-to-dict-converts-datetime-to-timestamp
    for result in results:
        result["datetime"] = result["datetime"].to_pydatetime()
    return results


def fetch_exchange(
    zone_key1: str = "JP-TH",
    zone_key2: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    if not session:
        session = Session()

    query_datetime = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y/%m/%d")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    return _fetch_exchange(session, query_datetime, sorted_zone_keys)


def fetch_exchange_forecast(
    zone_key1: str = "JP-TH",
    zone_key2: str = "JP-TK",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets exchange forecast between two specified zones."""
    if not session:
        session = Session()

    query_datetime = arrow.get(target_datetime).to("Asia/Tokyo").strftime("%Y/%m/%d")

    if query_datetime > arrow.get().to("Asia/Tokyo").strftime("%Y/%m/%d"):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected exchange"
        )

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    return _fetch_exchange(session, query_datetime, sorted_zone_keys)


def get_cookies(session: Session | None = None) -> cookies.RequestsCookieJar:
    if not session:
        session = Session()
    session.get("http://occtonet.occto.or.jp/public/dfw/RP11/OCCTO/SD/LOGIN_login")
    return session.cookies


def get_form_data(session: Session, exchange_id: int, datetime: str) -> dict[str, str]:
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
        "spcDay": datetime,
        "spcDayHdn": "",
        "tgtRkl": f"{exchange_id:02d}",
        "tgtRklHdn": "01,北海道・本州間電力連系設備,02,相馬双葉幹線,03,周波数変換設備,04,三重東近江線,05,南福光連系所・南福光変電所の連系設備,06,越前嶺南線,07,西播東岡山線・山崎智頭線,08,阿南紀北直流幹線,09,本四連系線,10,関門連系線,11,北陸フェンス",
        "transitionContextKey": "DEFAULT",
        "updDaytime": "",
    }

    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    response_content = r.json()

    if response_content["root"]["errMessage"]:
        raise ParserException(
            "occtonet.py",
            "Headers not available due to {}".format(
                response_content["root"]["errMessage"]
            ),
        )
    else:
        form_data["msgArea"] = response_content["root"]["bizRoot"]["header"]["msgArea"][
            "value"
        ]
        form_data["searchReqHdn"] = response_content["root"]["bizRoot"]["header"][
            "searchReqHdn"
        ]["value"]
        form_data["spcDayHdn"] = response_content["root"]["bizRoot"]["header"][
            "spcDayHdn"
        ]["value"]
        form_data["updDaytime"] = response_content["root"]["bizRoot"]["header"][
            "updDaytime"
        ]["value"]

    form_data["fwExtention.actionSubType"] = "ok"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    response_content = r.json()

    if response_content["root"]["errFields"]:
        raise ParserException(
            "occtonet.py",
            "Request token not available due to {}".format(
                response_content["root"]["errFields"]
            ),
        )
    else:
        form_data["downloadKey"] = response_content["root"]["bizRoot"]["header"][
            "downloadKey"
        ]["value"]
        form_data["requestToken"] = response_content["root"]["bizRoot"]["header"][
            "requestToken"
        ]["value"]
    return form_data


def _get_exchange(session: Session, form_data: dict[str, str], columns: list[str]):
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


def get_exchange(session: Session, form_data):
    return _get_exchange(session, form_data, ["対象日付", "対象時刻", "潮流実績"])


def get_exchange_fcst(session: Session, form_data):
    return _get_exchange(
        session, form_data, ["対象日付", "対象時刻", "計画潮流(順方向)"]
    )


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
