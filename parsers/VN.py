#!/usr/bin/env python3

import json
import zoneinfo
from datetime import datetime, timedelta
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    TotalConsumptionList,
)
from parsers.lib.exceptions import ParserException

## Vietnamese National Load Dispatch Center https://www.nldc.evn.vn/
# Access via day, can also parse historical data

tz = zoneinfo.ZoneInfo("Asia/Ho_Chi_Minh")
LIVE_DATA = {
    "consumption": "https://www.nldc.evn.vn/api/services/app/Pages/GetChartPhuTaiVM",
    "price": "https://www.nldc.evn.vn/api/services/app/Pages/GetChartGiaBienVM",
}

HISTORICAL_DATA = "https://www.nldc.evn.vn/api/services/app/Dashboard/GetBieuDoTuongQuanPT"  # + dd/mm/yyyy

ZONE_CODE = {ZoneKey("VN"): "HT"}


def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is None:
        live_consumption = fetch_live_consumption(session, logger)
        # Live data is empty at 00:00, resort to historical from previous day (which includes 00:00)
        if len(live_consumption) > 0:
            return live_consumption
        else:
            return fetch_historical_consumption(
                datetime.now().astimezone(tz) - timedelta(days=1), session, logger
            )
    else:
        return fetch_historical_consumption(target_datetime, session, logger)


def fetch_price(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is None:
        live_consumption = fetch_live_price(session, logger)
        # Live data is empty at 00:00, resort to historical from previous day (which includes 00:00)
        if len(live_consumption) > 0:
            return live_consumption
        else:
            return fetch_historical_price(
                datetime.now().astimezone(tz) - timedelta(days=1), session, logger
            )
    else:
        return fetch_historical_price(target_datetime, session, logger)


def fetch_historical_consumption(
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
):
    data_list = fetch_historical_data(session=session, target_datetime=target_datetime)
    result_list = TotalConsumptionList(logger)

    for data in data_list:
        result_list.append(
            datetime=datetime.fromisoformat(data["thoiGian"]).replace(tzinfo=tz),
            consumption=data["congSuat"],
            zoneKey=ZoneKey("VN"),
            source="nldc.evn.vn",
        )
    return result_list.to_list()


def fetch_historical_price(
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
):
    data_list = fetch_historical_data(session=session, target_datetime=target_datetime)

    result_list = PriceList(logger)

    for data in data_list:
        result_list.append(
            datetime=datetime.fromisoformat(data["thoiGian"]).replace(tzinfo=tz),
            currency="VND",
            price=data["giaBan"],
            zoneKey=ZoneKey("VN"),
            source="nldc.evn.vn",
        )
    return result_list.to_list()


def fetch_live_consumption(
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
):
    data_list = fetch_live_data("consumption", session)["phuTais"]

    result_list = TotalConsumptionList(logger)

    for data in data_list:
        result_list.append(
            datetime=datetime.fromisoformat(data["thoiGian"]).replace(tzinfo=tz),
            consumption=data[f"congSuat{ZONE_CODE[ZoneKey('VN')]}"],
            zoneKey=ZoneKey("VN"),
            source="nldc.evn.vn",
        )
    return result_list.to_list()


def fetch_live_price(
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
):
    data_list = fetch_live_data("price", session)["giaBiens"]

    result_list = PriceList(logger)

    for data in data_list:
        result_list.append(
            datetime=datetime.fromisoformat(data["thoiGian"]).replace(tzinfo=tz),
            price=data[f"giaBien{ZONE_CODE[ZoneKey('VN')]}"],
            currency="VND",
            zoneKey=ZoneKey("VN"),
            source="nldc.evn.vn",
        )
    return result_list.to_list()


def fetch_historical_data(
    target_datetime: datetime,
    session: Session = Session(),
):
    res = session.get(
        f"{HISTORICAL_DATA}?day={(target_datetime - timedelta(minutes=30)).strftime('%d/%m/%Y')}"
    )
    if not res.ok:
        raise ParserException(
            parser="VN.py", message=f"Request failed: {res.status_code}"
        )
    return json.loads(res.text)["result"]["data"]["phuTai"]


def fetch_live_data(data_type=str, session: Session = Session()):
    res = session.get(LIVE_DATA[data_type])
    if not res.ok:
        raise ParserException(
            parser="VN.py", message=f"Request failed: {res.status_code}"
        )
    return json.loads(res.text)["result"]["data"]


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_price() ->")
    print(fetch_price())
