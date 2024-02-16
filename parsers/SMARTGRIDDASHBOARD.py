from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType, ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IE_TZ = ZoneInfo("Europe/Dublin")

URL = "https://www.smartgriddashboard.com/DashboardService.svc/data"

SOURCE = "eirgridgroup.com"

KINDS_AREA_MAPPING = {
    "demand": "demandactual",
    "demand_forecast": "demandforecast",
    "wind": "windactual",
    "wind_forecast": "windforecast",
    "exchange": "interconnection",
    "generation": "generationactual",
}

REGION_MAPPING = {
    "IE": "ROI",
    "GB-NIR": "NI",
}

EXCHANGE_MAPPING = {
    ZoneKey("GB->IE"): {"key": "ROI", "exchange": "INTER_EWIC", "direction": 1},
    ZoneKey("GB->GB-NIR"): {"key": "NI", "exchange": "INTER_MOYLE", "direction": 1},
}


def get_datetime_params(datetime: datetime) -> dict:
    return {
        "datefrom": (datetime - timedelta(days=2)).strftime("%Y-%m-%d"),
        "dateto": (datetime + timedelta(days=1)).strftime("%Y-%m-%d"),
    }


def parse_datetime(datetime_str: str) -> datetime:
    return datetime.strptime(datetime_str, "%d-%b-%Y %H:%M:%S").replace(tzinfo=IE_TZ)


def fetch_data(
    target_datetime: datetime,
    zone_key: ZoneKey,
    kind: str,
    session: Session,
) -> list:
    """
    Gets values and corresponding datetimes for the specified data kind in ROI.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    assert isinstance(target_datetime, datetime)
    assert kind != ""
    assert session is not None

    resp: Response = session.get(
        url=URL,
        params={
            "area": KINDS_AREA_MAPPING[kind],
            "region": EXCHANGE_MAPPING[zone_key]["key"]
            if zone_key in EXCHANGE_MAPPING
            else REGION_MAPPING[zone_key],
            **get_datetime_params(target_datetime),
        },
    )
    try:
        data = resp.json().get("Rows", [])
    except Exception as e:
        raise ParserException(
            parser="SMARTGRIDDASHBOARD.py",
            message=f"{target_datetime}: {kind} data is not available for {zone_key}",
        ) from e
    return data


def parse_consumption(
    zone_key: ZoneKey,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
    forecast: bool,
) -> list:
    """gets forecasted consumption values for ROI"""

    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=IE_TZ)

    data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="demand_forecast" if forecast else "demand",
        session=session,
    )

    demandList = TotalConsumptionList(logger=logger)
    for item in data:
        demandList.append(
            zoneKey=zone_key,
            consumption=item["Value"],
            datetime=parse_datetime(item["EffectiveTime"]),
            source=SOURCE,
            sourceType=EventSourceType.forecasted
            if forecast
            else EventSourceType.measured,
        )
    return demandList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets values for wind production and estimates unknwon production as demand - wind - exchange"""
    if target_datetime is None:
        target_datetime = datetime.now(tz=IE_TZ)

    total_generation = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="generation",
        session=session,
    )

    wind_data = fetch_data(
        target_datetime=target_datetime, zone_key=zone_key, kind="wind", session=session
    )

    assert len(total_generation) > 0
    assert len(wind_data) > 0

    production = ProductionBreakdownList(logger=logger)

    for item in total_generation:
        dt = item["EffectiveTime"]
        wind_event_dt = [event for event in wind_data if event["EffectiveTime"] == dt]

        wind_prod = float(wind_event_dt[0]["Value"]) if wind_event_dt[0]["Value"] else 0

        productionMix = ProductionMix()
        if all([item["Value"], wind_prod]):
            productionMix.add_value("wind", wind_prod)
            productionMix.add_value("unknown", float(item["Value"]) - wind_prod)

        production.append(
            zoneKey=zone_key,
            production=productionMix,
            datetime=parse_datetime(dt),
            source=SOURCE,
        )

    return production.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetches exchanges values for the East-West (GB->IE) and Moyle (GB->GB-NIR)
    interconnectors.
    """
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=IE_TZ)

    exchangeKey = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if exchangeKey == "GB-NIR->IE":
        raise ParserException(
            parser="SMARTGRIDDASHBOARD.py",
            message="the GB-NIR_IE interconnection is unsupported.",
        )

    exchange_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=exchangeKey,
        kind="exchange",
        session=session,
    )

    exchangeList = ExchangeList(logger=logger)
    for exchange in exchange_data:
        flow = (
            exchange["Value"] * EXCHANGE_MAPPING[exchangeKey]["direction"]
            if exchange["Value"]
            else exchange["Value"]
        )

        exchangeList.append(
            zoneKey=exchangeKey,
            netFlow=flow,
            datetime=parse_datetime(exchange["EffectiveTime"]),
            source=SOURCE,
        )

    return exchangeList.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """gets consumption values for ROI"""
    return parse_consumption(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        forecast=False,
    )


@refetch_frequency(timedelta(days=1))
def fetch_consumption_forecast(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """gets forecasted consumption values for ROI"""
    return parse_consumption(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        forecast=True,
    )


@refetch_frequency(timedelta(days=1))
def fetch_wind_forecasts(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for forecasted wind produciton.
    """

    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=IE_TZ)

    wind_forecast_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="wind_forecast",
        session=session,
    )

    wind_forecast = ProductionBreakdownList(logger=logger)
    for item in wind_forecast_data:
        productionMix = ProductionMix()
        productionMix.add_value("wind", item["Value"], correct_negative_with_zero=True)
        wind_forecast.append(
            zoneKey=zone_key,
            production=productionMix,
            datetime=parse_datetime(item["EffectiveTime"]),
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return wind_forecast.to_list()


def fetch_total_generation(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for the total generation.
    This is the sum of all generation reported as a single value.
    """

    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=IE_TZ)

    generation_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="generation",
        session=session,
    )
    total_generation = TotalProductionList(logger=logger)
    for item in generation_data:
        total_generation.append(
            zoneKey=zone_key,
            value=item["Value"],
            datetime=parse_datetime(item["EffectiveTime"]),
            source=SOURCE,
            sourceType=EventSourceType.measured,
        )
    return total_generation.to_list()
