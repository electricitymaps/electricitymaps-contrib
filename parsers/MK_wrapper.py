from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional, Union

from pytz import utc
from requests import Session

from . import ENTSOE
from .lib.config import refetch_frequency

"""
This wrapper is used to fetch data from ENTSOE for the country of North Macedonia.
If no target_datetime is provided, the wrapper will provide a target datetime that is
24 hours in the past due to intermittent data availability.
"""


def modify_target_datetime(target_datetime: Optional[datetime]) -> datetime:
    if target_datetime is None:
        return datetime.now(tz=utc) - timedelta(hours=24)
    else:
        return target_datetime


@refetch_frequency(timedelta(days=2))
def fetch_consumption(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict, None]:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_consumption(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(timedelta(days=2))
def fetch_consumption_forecast(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_consumption_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(timedelta(days=2))
def fetch_generation_forecast(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_generation_forecast(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(timedelta(days=2))
def fetch_price(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_price(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_production(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )


@refetch_frequency(timedelta(days=2))
def fetch_wind_solar_forecasts(
    zone_key: str = "MK",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = modify_target_datetime(target_datetime)
    return ENTSOE.fetch_wind_solar_forecasts(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
