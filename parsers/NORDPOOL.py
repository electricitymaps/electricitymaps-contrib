from datetime import datetime
from enum import Enum
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.types import ZoneKey

NORDPOOL_BASE_URL = "https://www.nordpoolgroup.com/api/v2/"


class NORDPOOL_API_ENDPOINT(Enum):
    PRICE = "Auction/Prices/ByAreas"


class MARKET_TYPE(Enum):
    DAY_AHEAD = "DayAhead"


class CURRENCY(Enum):
    EUR = "EUR"
    DKK = "DKK"
    SEK = "SEK"
    NOK = "NOK"
    GBP = "GBP"


ZONE_MAPPING = {
    "AT": "AT",
    "BE": "BE",
    "DK-DK1": "DK1",
    "DK-DK2": "DK2",
    "DE": "GER",
    "EE": "EE",
    "FI": "FI",
    "FR": "FR",
    "GB": "UK",
    "LT": "LT",
    "LV": "LV",
    "NL": "NL",
    "NO-NO1": "NO1",
    "NO-NO2": "NO2",
    "NO-NO3": "NO3",
    "NO-NO4": "NO4",
    "NO-NO5": "NO5",
    "PL": "PL",
    "SE-SE1": "SE1",
    "SE-SE2": "SE2",
    "SE-SE3": "SE3",
    "SE-SE4": "SE4",
}


def _handle_status_code(response, logger: Logger):
    match response.status_code:
        case 200:
            return response.json()
        case 400:
            # Bad request
            raise ValueError(f"Bad request: {response.text}")
        case 401:
            # Unauthorized
            raise PermissionError(f"Unauthorized access: {response.text}")
        case 403:
            # Forbidden
            raise PermissionError(f"Forbidden access: {response.text}")
        case _:
            # Other errors
            raise Exception(
                f"Unexpected error: Code: {response.status_code}, Text: {response.text}"
            )


def query_nordpool(
    endpoint: NORDPOOL_API_ENDPOINT,
    params: dict[str, str],
    logger: Logger,
    session: Session | None = None,
):
    session = session or Session()
    _headers = {}
    response = session.get(f"{NORDPOOL_BASE_URL}{endpoint.value}", params=params)
    return _handle_status_code(response, logger)


def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = target_datetime or datetime.now()
    params = {
        "areas": ZONE_MAPPING[zone_key],
        "currency": CURRENCY.EUR.value,
        "market": MARKET_TYPE.DAY_AHEAD.value,
        "date": target_datetime.date().isoformat(),
    }
    _response = query_nordpool(NORDPOOL_API_ENDPOINT.PRICE, params, logger, session)
    return []
