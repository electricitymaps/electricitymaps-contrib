from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Literal

from requests import Session

from .ENTSOE import fetch_exchange as fetch_ENTSOE_exchange
from .ENTSOE import fetch_exchange_forecast as fetch_ENTSOE_exchange_forecast
from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

"""
Fetches data for the NO-NO4->SE-SE1 and NO-NO4->SE-SE2 exchanges
by wrapping the ENTSOE.py parser and combining the data from the two
to produce a single data list for the NO-NO4->SE exchange.
"""

EXCHANGE_FUNCTION_MAP: dict[str, Callable] = {
    "exchange": fetch_ENTSOE_exchange,
    "exchange_forecast": fetch_ENTSOE_exchange_forecast,
}


def fetch_data(
    zone_key1: str,
    zone_key2: str,
    session: Session | None,
    target_datetime: datetime | None,
    logger: Logger,
    exchange_type: Literal["exchange", "exchange_forecast"],
) -> list[dict]:
    if target_datetime is None:
        target_datetime = datetime.now(timezone.utc)

    # NO-NO4 to SE-SE1
    SE1_dataList = EXCHANGE_FUNCTION_MAP[exchange_type](
        zone_key1="NO-NO4",
        zone_key2="SE-SE1",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # NO-NO4 to SE-SE2
    SE2_dataList = EXCHANGE_FUNCTION_MAP[exchange_type](
        zone_key1="NO-NO4",
        zone_key2="SE-SE2",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    returnList: list[dict] = []

    # Compare the length and datetimes of the two data lists and
    # if they are the same combine the data from the two lists.
    if (
        len(SE1_dataList) == len(SE2_dataList)
        and SE1_dataList[0]["datetime"] == SE2_dataList[0]["datetime"]
        and SE1_dataList[-1]["datetime"] == SE2_dataList[-1]["datetime"]
    ):
        logger.info("Clean match! Merging data with zip")
        for SE1, SE2 in zip(SE1_dataList, SE2_dataList, strict=True):
            returnList.append(
                {
                    "datetime": SE1["datetime"],
                    "netFlow": SE1["netFlow"] + SE2["netFlow"],
                    "sortedZoneKeys": "NO-NO4->SE",
                    "source": SE1["source"],
                }
            )

    # Parse values from the two lists and loop over them to find missing datetimes
    # if the two lists are not of equal length and do not have the same datetimes.
    else:
        logger.info("Data mismatch! Recursively looping over lists to match data")
        for SE1_data in SE1_dataList:
            for SE2_data in SE2_dataList:
                if SE1_data["datetime"] == SE2_data["datetime"]:
                    returnList.append(
                        {
                            "datetime": SE1_data["datetime"],
                            "netFlow": SE1_data["netFlow"] + SE2_data["netFlow"],
                            "sortedZoneKeys": "NO-NO4->SE",
                            "source": SE1_data["source"],
                        }
                    )
    if returnList != []:
        return returnList
    else:
        raise ParserException(
            parser="NO-NO4_SE.py",
            message=f"No matching exchange data found between {zone_key1} and {zone_key2} at {target_datetime}.",
        )


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: str = "NO-NO4",
    zone_key2: str = "SE",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    return fetch_data(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        exchange_type="exchange",
    )


@refetch_frequency(timedelta(days=2))
def fetch_exchange_forecast(
    zone_key1: str = "NO-NO4",
    zone_key2: str = "SE",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    return fetch_data(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        exchange_type="exchange_forecast",
    )
