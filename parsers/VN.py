#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional, Union

import arrow
import pytz
from requests import Response, Session

from parsers.lib.exceptions import ParserException

## Vietnamese National Load Dispatch Center https://www.nldc.evn.vn/
# Access via day, can also parse historical data

tz = pytz.timezone("Asia/Ho_Chi_Minh")
base_url_from_type = {
    "consumption": "https://www.nldc.evn.vn/PhuTaiHandle.ashx?d=",  # + dd/mm/yyyy
    "price": "https://www.nldc.evn.vn/GiaBienHandle.ashx?d=",  # + dd/mm/yyyy
}


def fetch_latest_data(
    data_type: str,
    session: Session,
):
    """
    Fetch latest available
    """
    fetched_day = arrow.now(tz=tz)

    base_url = base_url_from_type[data_type]

    today_dt_str = fetched_day.format("DD/MM/YYYY")

    # Try fetch data for today.
    today_response: Response = session.get(base_url + today_dt_str)

    # Check if today's data is there.
    if today_response.ok and today_response.json() is not None:
        return fetched_day.floor("day"), today_response.json()

    # If it is too early in the day, it might not contain data yet. Get from yesterday.
    fetched_day = fetched_day.shift(days=-1)
    yesterday_dt_str = fetched_day.format("DD/MM/YYYY")

    yesterday_response: Response = session.get(base_url + yesterday_dt_str)
    # Check if yesterday's data is there.
    if yesterday_response.ok and yesterday_response.json() is not None:
        return fetched_day.floor("day"), yesterday_response.json()

    # Also no data from yesterday, cant fetch recent data.
    raise ParserException(
        parser="VN.py",
        message=(
            f"Requested recent data - request endpoint can't provide data for 2 days."
            f"Return codes: {today_response.status_code}, {yesterday_response.status_code} at {fetched_day}"
        ),
    )


def fetch_target_data(data_type: str, target_datetime, session: Session):
    """
    Fetch the day containing the given target_datetime.
    """

    # Convert timezone, and get the day
    target_datetime_vn = arrow.get(target_datetime).to(tz)

    fetched_day = target_datetime_vn.floor("day")
    target_dt_str = fetched_day.format("DD/MM/YYYY")

    target_response: Response = session.get(
        base_url_from_type[data_type] + target_dt_str
    )
    if target_response.ok and target_response.json() is not None:
        return fetched_day, target_response.json()

    # Requested data not available.
    raise ParserException(
        parser="VN.py",
        message=(
            f"Requested {target_datetime} - request endpoint can't provide data - {target_response.status_code}."
        ),
    )


def data_index_to_valid_time(base_day: datetime, idx: int):
    """
    Convert index in fetched data to associated time, given base date (day)
    Valid time of indices is: [0:30, 1:00, 1:30, ..., 23:30, 24:00]
    """
    idx_datetime = base_day.replace(
        hour=int((idx + 1) / 2), minute=(0 if idx % 2 else 30)
    ).floor("minute")

    return idx_datetime


def fetch_consumption(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:

    request_latest = target_datetime is None

    if request_latest:
        fetched_day, fetched_data = fetch_latest_data("consumption", session)

    else:
        # TODO API bug for past data:
        # data for given date can only be retrieved until the current hour.
        fetched_day, fetched_data = fetch_target_data(
            "consumption", target_datetime, session
        )

    # [0] = load of Northern Vietnam
    # [1] = load of Central Vietnam
    # [2] = load of Southern Vietnam
    # [3] = load of Vietnam (total)
    per_zone_load = {
        "VN-N": fetched_data["data"][0],
        "VN-C": fetched_data["data"][1],
        "VN-S": fetched_data["data"][2],
        "VN": fetched_data["data"][3],
    }

    result_list = []

    for i in range(len(per_zone_load[zone_key])):
        # Convert i to datetime
        i_datetime = data_index_to_valid_time(fetched_day, i)

        # Data also goes ~2h into the future! Seems to be some kind of prediction, since these
        # future values are changing until their valid time is reached.
        if request_latest and i_datetime > arrow.now(tz=tz):
            continue

        result_list.append(
            {
                "datetime": i_datetime.datetime,
                "consumption": per_zone_load[zone_key][i],
                "zoneKey": zone_key,
                "source": "nldc.evn.vn",
            }
        )

    if not len(result_list):
        raise ParserException(
            parser="VN.py",
            message=f"No valid consumption data for requested day found.",
        )

    return result_list


def fetch_price(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:

    request_latest = target_datetime is None

    if request_latest:
        fetched_day, fetched_data = fetch_latest_data("price", session)
    else:
        # TODO API bug for past data:
        # data for given date can only be retrieved until the current hour.
        fetched_day, fetched_data = fetch_target_data("price", target_datetime, session)

    # [0] = load of Northern Vietnam
    # [1] = load of Central Vietnam
    # [2] = load of Southern Vietnam
    per_zone_price = {
        "VN-N": fetched_data["data"][0],
        "VN-C": fetched_data["data"][1],
        "VN-S": fetched_data["data"][2]
        # no total VN data
    }

    result_list = []

    for i in range(len(per_zone_price[zone_key])):
        # Convert i to datetime
        i_datetime = data_index_to_valid_time(fetched_day, i)

        # Data also goes ~2h into the future! Seems to be some kind of prediction, since these
        # future values are changing until their valid time is reached.
        if request_latest and i_datetime > arrow.now(tz=tz):
            continue

        # faulty data at given time?
        if per_zone_price[zone_key][i] is None:
            continue

        result_list.append(
            {
                "datetime": i_datetime.datetime,
                "price": per_zone_price[zone_key][i],
                "currency": "VND",
                "zoneKey": zone_key,
                "source": "nldc.evn.vn",
            }
        )

    if len(result_list) == 0:
        raise ParserException(
            parser="VN.py", message=f"No valid prices for requested day found."
        )

    return result_list


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_price() ->")
    print(fetch_price())
