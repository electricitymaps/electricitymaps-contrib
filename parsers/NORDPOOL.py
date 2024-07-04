from datetime import datetime, timedelta
from enum import Enum
from logging import Logger, getLogger
from urllib.parse import urlencode

from lib.utils import get_token
from requests import Response, Session

from electricitymap.contrib.lib.types import ZoneKey

NORDPOOL_BASE_URL = "https://data-api.nordpoolgroup.com/api/v2/"

# Set this as a global const outside of the functions to cache the token for the current parser instance
NORDPOOL_TOKEN = None
NORDPOOL_TOKEN_EXPIRATION = None


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


def _generate_new_nordpool_token(session: Session | None = None) -> str:
    global NORDPOOL_TOKEN_EXPIRATION
    session = session or Session()
    URL = "https://sts.nordpoolgroup.com/connect/token"
    username = get_token("EMAPS_NORDPOOL_USERNAME")
    password = get_token("EMAPS_NORDPOOL_PASSWORD")
    headers = {
        "accept": "application/json",
        "Authorization": "Basic Y2xpZW50X2F1Y3Rpb25fYXBpOmNsaWVudF9hdWN0aW9uX2FwaQ==",  # This is a public key listed in the Nordpool API documentation
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "password",
        "scope": "auction_api",
        "username": username,
        "password": password,
    }
    encoded_credentials = urlencode(data)
    response = session.post(URL, headers=headers, data=encoded_credentials)
    response = _handle_status_code(response, getLogger(__name__))
    NORDPOOL_TOKEN_EXPIRATION = datetime.now() + timedelta(
        seconds=response.json()["expires_in"]
    )

    return response.json()["access_token"]


def _get_token() -> str:
    global NORDPOOL_TOKEN
    global NORDPOOL_TOKEN_EXPIRATION
    if (
        NORDPOOL_TOKEN is None
        or NORDPOOL_TOKEN_EXPIRATION is None
        or datetime.now() > NORDPOOL_TOKEN_EXPIRATION - timedelta(minutes=5)
    ):
        NORDPOOL_TOKEN = _generate_new_nordpool_token()
    return NORDPOOL_TOKEN


def _handle_status_code(response: Response, logger: Logger) -> Response:
    match response.status_code:
        case 200:
            return response
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
    TOKEN = _get_token()
    session = session or Session()
    headers = {
        "Authorization": f"Bearer {TOKEN}",
    }

    response = session.get(
        f"{NORDPOOL_BASE_URL}{endpoint.value}", params=params, headers=headers
    )

    response = _handle_status_code(response, logger)
    return response


def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = target_datetime or datetime.now()
    params = {
        "areas": f"{ZONE_MAPPING[zone_key]}",
        "currency": CURRENCY.EUR.value,
        "market": MARKET_TYPE.DAY_AHEAD.value,
        "date": target_datetime.date().isoformat(),
    }
    response = query_nordpool(NORDPOOL_API_ENDPOINT.PRICE, params, logger, session)
    return []


fetch_price(
    ZoneKey("SE-SE1"),
    session=Session(),
    target_datetime=datetime.now(),
    logger=getLogger(__name__),
)
