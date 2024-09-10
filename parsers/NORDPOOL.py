from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import Logger, getLogger

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import PriceList
from electricitymap.contrib.lib.types import ZoneKey

from .lib.utils import get_token

NORDPOOL_BASE_URL = "https://data-api.nordpoolgroup.com/api/v2/"


@dataclass
class NordpoolToken:
    token: str
    expiration: datetime

    @property
    def is_expired(self) -> bool:
        return datetime.now(tz=timezone.utc) > self.expiration + timedelta(minutes=5)


CURRENT_TOKEN: NordpoolToken | None = None

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


def _generate_new_nordpool_token(session: Session) -> NordpoolToken:
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
    token_data = response.json()
    token = NordpoolToken(
        token=token_data["access_token"],
        expiration=datetime.now(tz=timezone.utc)
        + timedelta(seconds=token_data["expires_in"]),
    )

    return token


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
def zulu_to_utc(datetime_string: str) -> str:
    """Converts a zulu time string to a UTC time string."""
    return datetime_string.replace("Z", "+00:00")


def _query_nordpool(
    endpoint: NORDPOOL_API_ENDPOINT,
    params: dict[str, str],
    logger: Logger,
    session: Session,
):
    global CURRENT_TOKEN
    if CURRENT_TOKEN is None or CURRENT_TOKEN.is_expired:
        CURRENT_TOKEN = _generate_new_nordpool_token(session)
    headers = {
        "Authorization": f"Bearer {CURRENT_TOKEN.token}",
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
    session = session or Session()
    target_datetime = target_datetime or datetime.now()
    params = {
        "areas": f"{ZONE_MAPPING[zone_key]}",
        "currency": CURRENCY.EUR.value
        if zone_key != ZoneKey("GB")  # GB uses GBP not EUR
        else CURRENCY.GBP.value,
        "market": MARKET_TYPE.DAY_AHEAD.value
        if zone_key != ZoneKey("GB")  # GB uses it's own 30 minute TMU day ahead market
        else MARKET_TYPE.GB_DAY_AHEAD.value,
        "date": target_datetime.date().isoformat(),
    }
    response_target = _query_nordpool(
        NORDPOOL_API_ENDPOINT.PRICE, params, logger, session
    )
    params["date"] = (target_datetime + timedelta(days=1)).date().isoformat()
    response_target_day_ahead = _query_nordpool(
        NORDPOOL_API_ENDPOINT.PRICE, params, logger, session
    )
    price_data_target: PriceList = _parse_price(response_target, logger)
    price_data_target_day_ahead: PriceList = _parse_price(
        response_target_day_ahead, logger
    )

    return (price_data_target + price_data_target_day_ahead).to_list()
