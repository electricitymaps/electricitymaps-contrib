#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional
from urllib.parse import urlencode

# The arrow library is used to handle datetimes
import arrow
import pytz
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.lib.types import ZoneKey

from .lib.exceptions import ParserException
from .lib.utils import get_token

TIMEZONE = pytz.timezone("Europe/Madrid")

# Map each exchange to the ID used in the API. 10278 is used for Andorra->Spain until 10210 returns data correctly
EXCHANGE_ID_MAP = {
    "AD->ES": "10278",
    "ES->MA": "10209",
}


def format_url(target_datetime: datetime, ID: str):
    start_date = (target_datetime - timedelta(hours=24)).isoformat()
    end_date = target_datetime.isoformat()
    dates = {"start_date": start_date, "end_date": end_date}
    query = urlencode(dates)
    return f"https://api.esios.ree.es/indicators/{ID}?{query}"


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    # Get ESIOS token
    token = get_token("ESIOS_TOKEN")

    ses = session or Session()
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    # Request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json; application/vnd.esios-api-v2+json",
        "x-api-key": token,
    }

    zone_key = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if zone_key not in EXCHANGE_ID_MAP.keys():
        raise ParserException(
            "ESIOS.py",
            f"This parser cannot parse data between {zone_key1} and {zone_key2}.",
        )
    url = format_url(target_datetime, EXCHANGE_ID_MAP[zone_key])

    response: Response = ses.get(url, headers=headers)
    if response.status_code != 200 or not response.text:
        raise ParserException(
            "ESIOS", "Response code: {0}".format(response.status_code)
        )

    json = response.json()
    values = json["indicator"]["values"]
    if not values:
        raise ParserException("ESIOS", "No values received")
    exchanges = ExchangeList(logger)

    for value in values:
        # Get last value in datasource
        # Datasource negative value is exporting, positive value is importing
        # If Spain is the second country, the value must be opposite
        if zone_key.startswith("ES"):
            net_flow = -value["value"]
        else:
            net_flow = value["value"]

        exchanges.append(
            zoneKey=zone_key,
            datetime=arrow.get(value["datetime_utc"]).datetime,
            netFlow=net_flow,
            source="api.esios.ree.es",
        )

    return exchanges.to_list()


if __name__ == "__main__":
    session = Session()
    print(fetch_exchange(ZoneKey("ES"), ZoneKey("MA"), session))
    print("fetch_exchange(ES, MA)")
    print(fetch_exchange(ZoneKey("AD"), ZoneKey("ES"), session))
    print("fetch_exchange(AD, ES)")
