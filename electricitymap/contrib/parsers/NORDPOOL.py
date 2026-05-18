import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from logging import Logger, getLogger

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeAtcList,
    ExchangeList,
    IntradayContractStatisticsList,
    PriceList,
)
from electricitymap.contrib.parsers.lib.nordpool_intraday_schemas import (
    STATS_AREAS,
    ContractStatisticsResponse,
)
from electricitymap.contrib.types import AtcType, ZoneKey

from .lib.config import refetch_frequency
from .lib.utils import get_token

"""
Parser for the Nordpool API.
API documentation: https://data-api.nordpoolgroup.com/index.html
"""

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
    EXCHANGE = "PowerSystem/Exchanges/ByAreas"
    INTRADAY_CONTRACT_STATISTICS = "Intraday/ContractStatistics/ByAreas"
    CAPACITY = "Auction/Capacities/ByAreas"


class MARKET_TYPE(Enum):
    DAY_AHEAD = "DayAhead"
    GB_DAY_AHEAD = "GbHalfHour_DayAhead"


class CURRENCY(Enum):
    EUR = "EUR"
    DKK = "DKK"
    SEK = "SEK"
    NOK = "NOK"
    GBP = "GBP"
    PLN = "PLN"
    RON = "RON"


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
    "RU-1": "RU",
    "RU-KGD": "LKAL",
}

INVERTED_ZONE_MAPPING = {value: key for key, value in ZONE_MAPPING.items()}


# Sorted "A->B" → (query_area on zone1's side, counterpart on zone2's side).
# That convention lets the parser map exports → capacityExport and imports →
# capacityImport directly, no flip. Nordic AC zones return "Missing", so
# their side uses a cable code (NO2_NK, SE3_FS, DK1_SB, ...).
NORDPOOL_BORDERS: dict[ZoneKey, tuple[str, str]] = {
    ZoneKey("DE->NO-NO2"): ("GER", "NO2_NK"),
    ZoneKey("DK-DK1->NO-NO2"): ("DK1_SK", "NO2_SK"),
    ZoneKey("NL->NO-NO2"): ("NL", "NO2_ND"),
    ZoneKey("SE-SE3->SE-SE4"): ("SE3_SWL", "SE4_SWL"),
    ZoneKey("DE->SE-SE4"): ("GER", "SE4_BC"),
    ZoneKey("LT->SE-SE4"): ("LT", "SE4_NB"),
    ZoneKey("PL->SE-SE4"): ("PL", "SE4_SP"),
    ZoneKey("EE->FI"): ("EE", "FI_EL"),
    ZoneKey("FI->SE-SE3"): ("FI_FS", "SE3_FS"),
    ZoneKey("DE->DK-DK1"): ("GER", "DK1_DE"),
    ZoneKey("DK-DK1->DK-DK2"): ("DK1_SB", "DK2_SB"),
    ZoneKey("DK-DK1->NL"): ("DK1_CO", "NL"),
    ZoneKey("DK-DK1->SE-SE3"): ("DK1_KS", "SE3_KS"),
    ZoneKey("DE->DK-DK2"): ("GER", "DK2_KO"),
    ZoneKey("EE->LV"): ("EE", "LV"),
    ZoneKey("LT->LV"): ("LT", "LV"),
    ZoneKey("LT->PL"): ("LT", "PL"),
}


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


@refetch_frequency(timedelta(days=1))
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


def _parse_exchange(response: Response, logger: Logger, target_zone) -> ExchangeList:
    exchange_list = ExchangeList(logger)
    json = response.json()[0]
    exchanges = json["exchanges"]
    for exchange in exchanges:
        for connection in exchange["byConnections"]:
            if connection["area"] == ZONE_MAPPING[target_zone]:
                exchange_list.append(
                    zoneKey=ZoneKey(
                        f"{INVERTED_ZONE_MAPPING[json['deliveryArea']]}->{INVERTED_ZONE_MAPPING[connection['area']]}"
                    ),
                    netFlow=-connection[
                        "netPosition"
                    ],  # Import is positive, export is negative
                    datetime=datetime.fromisoformat(
                        zulu_to_utc(exchange["deliveryStart"])
                    ),
                    source=SOURCE,
                )
    return exchange_list


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets exchange status between two specified zones.
    Only supports Nordpool zones.
    """
    session = session or Session()
    target_datetime = target_datetime or datetime.now()
    params = {
        "areas": f"{ZONE_MAPPING[zone_key1]}",
        "date": target_datetime.date().isoformat(),
    }
    response_target = _query_nordpool(
        NORDPOOL_API_ENDPOINT.EXCHANGE, params, logger, session
    )
    exchange_data = _parse_exchange(
        response=response_target,
        logger=logger,
        target_zone=zone_key2,
    )
    # Request the day before as well so we get overlapping data
    params["date"] = (target_datetime - timedelta(days=1)).date().isoformat()
    response_target_day_before = _query_nordpool(
        NORDPOOL_API_ENDPOINT.EXCHANGE, params, logger, session
    )
    exchange_data_day_before = _parse_exchange(
        response=response_target_day_before,
        logger=logger,
        target_zone=zone_key2,
    )
    # Combines both ExchangeLists and return them as a native list.
    return (exchange_data + exchange_data_day_before).to_list()


_INTER_AREA_SLEEP_S = 0.5


@refetch_frequency(timedelta(days=1))
def fetch_intraday_contract_statistics(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Fetch Nord Pool intraday ContractStatistics for the given zone and date.

    For DE: fetches all 5 TSO areas (GER, 50Hz, AMP, TTG, TBW) for the target
    CET date and emits one IntradayContractStatistics event per (area, contract).
    Raises ValidationError if the API payload drifts.
    """
    if zone_key != ZoneKey("DE"):
        raise NotImplementedError(
            f"fetch_intraday_contract_statistics is not yet implemented for zone: {zone_key}"
        )

    session = session or Session()
    target_datetime = target_datetime or datetime.now(tz=timezone.utc)

    # Convert to CET date for the API call.
    from zoneinfo import ZoneInfo

    cet = ZoneInfo("Europe/Berlin")
    delivery_date = target_datetime.astimezone(cet).date()

    intraday_list = IntradayContractStatisticsList(logger)

    for i, area in enumerate(STATS_AREAS):
        if i > 0:
            time.sleep(_INTER_AREA_SLEEP_S)

        params = {"areas": area, "date": delivery_date.isoformat()}
        response = _query_nordpool(
            NORDPOOL_API_ENDPOINT.INTRADAY_CONTRACT_STATISTICS, params, logger, session
        )
        # Raises ValidationError on schema drift — caller (feeder) catches and skips area.
        area_result = ContractStatisticsResponse.parse_obj(response.json())

        for area_data in area_result.__root__:
            price_unit = area_data.priceUnit  # e.g. "EUR/MWh"
            currency = price_unit.split("/")[0] if "/" in price_unit else price_unit
            api_updated_at = area_data.updatedAt

            for contract in area_data.contracts:
                intraday_list.append(
                    zoneKey=zone_key,
                    area=area,
                    apiUpdatedAt=api_updated_at,
                    currency=currency,
                    priceUnitRaw=price_unit,
                    deliveryStart=contract.deliveryStart,
                    deliveryEnd=contract.deliveryEnd,
                    contractId=contract.contractId,
                    contractName=contract.contractName,
                    contractOpenTime=contract.contractOpenTime,
                    contractCloseTime=contract.contractCloseTime,
                    isLocalContract=contract.isLocalContract,
                    vwap=contract.averagePrice,
                    vwap1hBeforeClose=contract.averagePriceLast1H,
                    vwap3hBeforeClose=contract.averagePriceLast3H,
                    openPrice=contract.openPrice,
                    closePrice=contract.closePrice,
                    highPrice=contract.highPrice,
                    lowPrice=contract.lowPrice,
                    openTradeTime=contract.openTradeTime,
                    closeTradeTime=contract.closeTradeTime,
                    volume=contract.volume,
                    buyVolume=contract.buyVolume,
                    sellVolume=contract.sellVolume,
                    source="nordpool",
                )

    return intraday_list.to_list()


def _find_connection_capacity(
    connections: list[dict] | None, counterpart: str
) -> float | None:
    if not connections:
        return None
    for connection in connections:
        if connection.get("area") == counterpart:
            return connection.get("capacity")
    return None


def _parse_capacity(
    response: Response,
    logger: Logger,
    sorted_zone_key: ZoneKey,
    counterpart: str,
) -> ExchangeAtcList:
    """Parse a Nordpool capacity response into ExchangeAtc events.

    Per NORDPOOL_BORDERS convention, the query is always issued from zone1's
    side, so Nordpool's perspective lines up directly with the sorted-pair
    direction: exportsByConnection = zone1→zone2 (capacityExport),
    importsByConnection = zone2→zone1 (capacityImport).
    """
    capacity_list = ExchangeAtcList(logger)
    json = response.json()
    if not json:
        return capacity_list
    entry = json[0]
    # Nordpool returns status="Missing" for areas it does not publish on the
    # requested date; treat as a no-op rather than an error so the caller can
    # combine multiple days without one missing day taking down the rest.
    if entry.get("status") != "Available":
        return capacity_list

    for period in entry.get("capacities") or []:
        capacity_export = _find_connection_capacity(
            period.get("exportsByConnection"), counterpart
        )
        capacity_import = _find_connection_capacity(
            period.get("importsByConnection"), counterpart
        )
        if capacity_export is None and capacity_import is None:
            continue

        capacity_list.append(
            zoneKey=sorted_zone_key,
            datetime=datetime.fromisoformat(zulu_to_utc(period["deliveryStart"])),
            source=SOURCE,
            capacityExport=capacity_export,
            capacityImport=capacity_import,
            atcType=AtcType.COORDINATED_NTC,
        )
    return capacity_list


@refetch_frequency(timedelta(days=2))
def fetch_exchange_available_transfer_capacity(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Day-ahead Available Transfer Capacity (ATC) from Nordpool.

    ATC is the capacity actually offered to the SDAC day-ahead auction after
    long-term physical transmission rights have been allocated and a
    transmission reliability margin subtracted.
    """
    sorted_pair = sorted([zone_key1, zone_key2])
    sorted_zone_key = ZoneKey(f"{sorted_pair[0]}->{sorted_pair[1]}")
    border = NORDPOOL_BORDERS.get(sorted_zone_key)
    if border is None:
        raise NotImplementedError(
            f"Nordpool ATC is not configured for border {sorted_zone_key}; "
            f"add an entry to NORDPOOL_BORDERS if Nordpool publishes it."
        )
    query_area, counterpart = border

    session = session or Session()
    target_datetime = target_datetime or datetime.now()

    params = {
        "areas": query_area,
        "market": MARKET_TYPE.DAY_AHEAD.value,
        "date": target_datetime.date().isoformat(),
    }
    response_target = _query_nordpool(
        NORDPOOL_API_ENDPOINT.CAPACITY, params, logger, session
    )
    capacities_target = _parse_capacity(
        response_target, logger, sorted_zone_key, counterpart
    )

    # Day-ahead publication: also fetch tomorrow so freshly-published capacity
    # for next-day delivery is captured. Mirrors fetch_price's 2-day window.
    params["date"] = (target_datetime + timedelta(days=1)).date().isoformat()
    response_day_ahead = _query_nordpool(
        NORDPOOL_API_ENDPOINT.CAPACITY, params, logger, session
    )
    capacities_day_ahead = _parse_capacity(
        response_day_ahead, logger, sorted_zone_key, counterpart
    )

    return (capacities_target + capacities_day_ahead).to_list()


# For debugging purposes
if __name__ == "__main__":
    print(
        fetch_intraday_contract_statistics(
            zone_key=ZoneKey("DE"),
            target_datetime=datetime.now(tz=timezone.utc),
        )
    )
