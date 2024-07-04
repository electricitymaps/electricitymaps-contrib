from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from logging import Logger, getLogger

from lib.utils import get_token
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import PriceList
from electricitymap.contrib.lib.types import ZoneKey

NORDPOOL_BASE_URL = "https://data-api.nordpoolgroup.com/api/v2/"

# Set this as a global const outside of the functions to cache the token for the current parser instance
NORDPOOL_TOKEN = None
NORDPOOL_TOKEN_EXPIRATION = None

SOURCE = "nordpool.com"


class NORDPOOL_API_ENDPOINT(Enum):
    PRICE = "Auction/Prices/ByAreas"


class MARKET_TYPE(Enum):
    DAY_AHEAD = "DayAhead"
    GB_DAY_AHEAD = "GbHalfHour_DayAhead"


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

INVERTED_ZONE_MAPPING = {value: key for key, value in ZONE_MAPPING.items()}


def _generate_new_nordpool_token(session: Session | None = None) -> str:
    global NORDPOOL_TOKEN_EXPIRATION
    session = session or Session()
    URL = "https://sts.nordpoolgroup.com/connect/token"
    username = get_token("EMAPS_NORDPOOL_USERNAME")
    password = get_token("EMAPS_NORDPOOL_PASSWORD")
    headers = {
        "accept": "application/json",
        "Authorization": "Basic Y2xpZW50X21hcmtldGRhdGFfYXBpOmNsaWVudF9tYXJrZXRkYXRhX2FwaQ==",  # This is a public key listed in the Nordpool API documentation
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "password",
        "scope": "marketdata_api",
        "username": username,
        "password": password,
    }
    response = session.post(URL, headers=headers, data=data)
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


# TODO: Remove this when we run on Python 3.11 or above
@lru_cache(maxsize=8)
def zulu_to_utc(datetime_string: str) -> str:
    """Converts a zulu time string to a UTC time string."""
    return datetime_string.replace("Z", "+00:00")


def _query_nordpool(
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


def _parse_price(response: Response, logger: Logger) -> PriceList:
    price_list = PriceList(logger)
    json = response.json()[0]
    prices = json["prices"]
    for price in prices:
        price_list.append(
            zoneKey=ZoneKey(INVERTED_ZONE_MAPPING[json["deliveryArea"]]),
            price=price["price"],
            datetime=datetime.fromisoformat(zulu_to_utc(price["deliveryStart"])),
            currency=json["currency"],
            source=SOURCE,
        )
    return price_list


def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = target_datetime or datetime.now()
    params = {
        "areas": f"{ZONE_MAPPING[zone_key]}",
        "currency": CURRENCY.EUR.value
        if zone_key != ZoneKey("GB")
        else CURRENCY.GBP.value,
        "market": MARKET_TYPE.DAY_AHEAD.value
        if zone_key != ZoneKey("GB")
        else MARKET_TYPE.GB_DAY_AHEAD.value,
        "date": target_datetime.date().isoformat(),
    }
    response = _query_nordpool(NORDPOOL_API_ENDPOINT.PRICE, params, logger, session)
    price_data: PriceList = _parse_price(response, logger)
    return price_data.to_list()
