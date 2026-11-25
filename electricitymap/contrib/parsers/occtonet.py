#!/usr/bin/env python3
from datetime import datetime, timedelta
from io import StringIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session, cookies

from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.types import ZoneKey

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
# Columns of the OCCTO interconnection CSV
DATE_COLUMN = "対象日付"  # target date
TIME_COLUMN = "対象時刻"  # target time
MEASURED_FLOW_COLUMN = "潮流実績"  # measured flow
PLANNED_FLOW_COLUMN = "計画潮流(順方向)"  # planned (scheduled) flow, signed

ZONE_INFO = ZoneInfo("Asia/Tokyo")


def _fetch_exchange(
    session: Session,
    query_date: str,
    sorted_zone_keys: ZoneKey,
    flow_column: str,
    source_type: EventSourceType,
    logger: Logger,
) -> ExchangeList:
    # This authorises subsequent calls
    get_cookies(session)

    # Some exchanges are made of several interconnection lines: their flows are summed.
    flows: pd.Series | None = None
    for exchange_id in EXCHANGE_MAPPING[sorted_zone_keys]:
        form_data = get_form_data(session, exchange_id, query_date)
        line_flows = _get_exchange(session, form_data, flow_column)
        if line_flows.empty:
            # A line can publish nothing for a whole day (e.g. line 05 of JP-CB->JP-HR):
            # skip it instead of discarding the other lines.
            continue
        # Keep only the timestamps reported by every line, never a partial sum.
        flows = line_flows if flows is None else flows.add(line_flows).dropna()

    exchanges = ExchangeList(logger)
    if flows is None:
        return exchanges
    direction = -1 if sorted_zone_keys in FLOWS_TO_REVERT else 1
    for timestamp, net_flow in flows.items():
        exchanges.append(
            zoneKey=sorted_zone_keys,
            datetime=timestamp.to_pydatetime(),
            netFlow=direction * float(net_flow),
            source=SOURCE_URL,
            sourceType=source_type,
        )
    return exchanges


def _query_date(target_datetime: datetime | None) -> str:
    if target_datetime is None:
        return datetime.now(ZONE_INFO).strftime("%Y/%m/%d")
    return target_datetime.astimezone(ZONE_INFO).strftime("%Y/%m/%d")


def fetch_exchange(
    zone_key1: ZoneKey = ZoneKey("JP-TH"),
    zone_key2: ZoneKey = ZoneKey("JP-TK"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    return _fetch_exchange(
        session or Session(),
        _query_date(target_datetime),
        sorted_zone_keys,
        MEASURED_FLOW_COLUMN,
        EventSourceType.measured,
        logger,
    ).to_list()


def fetch_exchange_forecast(
    zone_key1: ZoneKey = ZoneKey("JP-TH"),
    zone_key2: ZoneKey = ZoneKey("JP-TK"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Gets the planned power exchange (in MW) between two zones for the target day."""
    query_date = _query_date(target_datetime)
    if query_date > _query_date(None):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected exchange"
        )

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    return _fetch_exchange(
        session or Session(),
        query_date,
        sorted_zone_keys,
        PLANNED_FLOW_COLUMN,
        EventSourceType.forecasted,
        logger,
    ).to_list()


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


def _parse_datetime(date: str, time: str) -> datetime:
    """
    Expects arguments like "2024/12/23" and "00:05", including the edge case 24:00
    which is the same as 00:00 of the subsequent date.
    """
    if time == "24:00":
        dt = datetime.strptime(f"{date} 00:00", "%Y/%m/%d %H:%M") + timedelta(days=1)
    else:
        dt = datetime.strptime(f"{date} {time}", "%Y/%m/%d %H:%M")
    return dt.replace(tzinfo=ZONE_INFO)


def _get_exchange(
    session: Session, form_data: dict[str, str], flow_column: str
) -> pd.Series:
    """Downloads the CSV of one interconnection line: a flow (MW) per datetime."""
    form_data["fwExtention.actionSubType"] = "download"
    r = session.post(
        "https://occtonet3.occto.or.jp/public/dfw/RP11/OCCTO/SD/CA01S070C",
        data=form_data,
    )
    r.encoding = "shift-jis"
    df = pd.read_csv(StringIO(r.text), delimiter=",")
    df = df[[DATE_COLUMN, TIME_COLUMN, flow_column]].dropna()
    index = pd.Index(
        [
            _parse_datetime(date, time)
            for date, time in zip(df[DATE_COLUMN], df[TIME_COLUMN], strict=True)
        ],
        name="datetime",
    )
    return pd.Series(df[flow_column].astype(float).to_numpy(), index=index)


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
