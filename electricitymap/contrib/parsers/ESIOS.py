#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from time import sleep
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from electricitymap.contrib.lib.models.event_lists import ExchangeList
from electricitymap.contrib.types import ZoneKey

from .lib.exceptions import ParserException
from .lib.utils import get_token

TIMEZONE = ZoneInfo("Europe/Madrid")

# Map each exchange to the ID used in the API
EXCHANGE_ID_MAP = {
    "AD->ES": "10278",  # Switch to 10210 when it has data
    "ES->MA": "10209",
}

# Threshold date for ES->MA: from 2022-05-24T10:00:00.000+02:00 onwards, factor is 4 (15 min intervals)
# Before this date, factor is 1 (hourly intervals)
# Convert to UTC for comparison: 2022-05-24T10:00:00+02:00 = 2022-05-24T08:00:00+00:00
ES_MA_FACTOR_THRESHOLD = datetime(2022, 5, 24, 8, 0, 0, tzinfo=ZoneInfo("UTC"))


def get_exchange_multiplication_factor(
    zone_key: ZoneKey, exchange_datetime: datetime
) -> int:
    """
    Get the multiplication factor to adjust from MWh to MW.
    Depends on the time granularity of the API for each request.
    E.g ES->MA is 4 because the API returns 15 minutes intervals data (15 min = 1/4 of an hour; P=E/t).
    """
    if zone_key == "ES->MA":
        # From 2022-05-24T10:00:00.000+02:00 onwards, use factor 4 (15 min intervals)
        # Before this date, use factor 1 (hourly intervals)
        if exchange_datetime >= ES_MA_FACTOR_THRESHOLD:
            return 4
        else:
            return 1
    elif zone_key == "AD->ES":
        return 1
    else:
        raise ParserException(
            "ESIOS.py",
            f"Unknown exchange {zone_key} for multiplication factor.",
        )


def format_url(target_datetime: datetime, ID: str):
    start_date = (target_datetime - timedelta(hours=24)).isoformat()
    end_date = target_datetime.isoformat()
    dates = {"start_date": start_date, "end_date": end_date}
    query = urlencode(dates)
    return f"https://api.esios.ree.es/indicators/{ID}?{query}"


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    # Get ESIOS token
    token = get_token("ESIOS_TOKEN")

    # Only create a new session if one wasn't provided
    # This allows tests to pass in a session with mock adapters
    ses = session or Session()
    is_new_session = session is None

    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    # Request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json; application/vnd.esios-api-v2+json",
        "x-api-key": token,
    }

    zone_key = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    if zone_key not in EXCHANGE_ID_MAP:
        raise ParserException(
            "ESIOS.py",
            f"This parser cannot parse data between {zone_key1} and {zone_key2}.",
        )
    url = format_url(target_datetime, EXCHANGE_ID_MAP[zone_key])

    if is_new_session:
        # Configure retry strategy for HTTP status code errors
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[
                429,
                500,
                502,
                503,
                504,
            ],
            allowed_methods=["GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        ses.mount("https://", adapter)
        ses.mount("http://", adapter)

    # Manual retry loop with exponential backoff for connection/timeout errors
    # This gives us better control over retry behavior for network issue
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response: Response = ses.get(url, headers=headers, timeout=(30, 30))
            if response.status_code != 200 or not response.text:
                raise ParserException("ESIOS", f"Response code: {response.status_code}")
            break
        except (
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ) as e:
            if attempt < max_retries - 1:
                wait_time = 2**attempt
                logger.warning(
                    f"Connection error fetching ESIOS data (attempt {attempt + 1}/{max_retries}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                sleep(wait_time)
            else:
                logger.error(
                    f"Failed to fetch ESIOS data after {max_retries} attempts: {e}"
                )
                raise ParserException(
                    "ESIOS",
                    f"Connection failed after {max_retries} retries: {e}",
                ) from e
        except requests.exceptions.RequestException as e:
            raise ParserException("ESIOS", f"Request failed: {e}") from e

    json = response.json()
    values = json["indicator"]["values"]
    if not values:
        raise ParserException("ESIOS", "No values received")
    exchanges = ExchangeList(logger)

    for value in values:
        exchange_datetime = datetime.fromisoformat(
            value["datetime_utc"].replace("Z", "+00:00")
        )

        # Get last value in datasource
        # Datasource negative value is exporting, positive value is importing
        # If Spain is the first zone invert the values to match Electricity Maps schema
        net_flow = (
            -value["value"] if zone_key.partition("->")[0] == "ES" else value["value"]
        )

        net_flow *= get_exchange_multiplication_factor(zone_key, exchange_datetime)

        exchanges.append(
            zoneKey=zone_key,
            datetime=exchange_datetime,
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
