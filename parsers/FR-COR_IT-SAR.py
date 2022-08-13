from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Callable, Dict, List, Optional, TypedDict

from requests import Session

from .ENTSOE import fetch_exchange as fetch_ENTSOE_exchange
from .ENTSOE import fetch_exchange_forecast as fetch_ENTSOE_exchange_forecast
from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

"""
Fetches data for the IT-SACOAC->IT-SAR and IT-SACODC->IT-SAR exchanges
by wrapping the ENTSOE.py parser and combining the data from the two
to produce a single data list for the FR-COR->IT-SAR exchange.
"""

EXCHANGE_FUNCTION_MAP: Dict[str, Callable] = {
    "exchange": fetch_ENTSOE_exchange,
    "exchange_forecast": fetch_ENTSOE_exchange_forecast,
}


def fetch_data(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session],
    target_datetime: Optional[datetime],
    logger: Logger,
    type: str,
) -> List[dict]:

    if target_datetime is None:
        target_datetime = datetime.utcnow()

    # IT-SACOAC to IT-SAR
    AC_dataList = EXCHANGE_FUNCTION_MAP[type](
        zone_key1="FR-COR-AC",
        zone_key2="IT-SAR",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # IT-SACODC to IT-SAR
    DC_dataList = EXCHANGE_FUNCTION_MAP[type](
        zone_key1="FR-COR-DC",
        zone_key2="IT-SAR",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )

    returnList: List[dict] = []
    for AC_data in AC_dataList:
        for DC_data in DC_dataList:
            if AC_data["datetime"] == DC_data["datetime"]:
                returnList.append(
                    {
                        "datetime": AC_data["datetime"],
                        "source": AC_data["source"],
                        "sortedZoneKeys": "FR-COR->IT-SAR",
                        "netFlow": AC_data["netFlow"] + DC_data["netFlow"],
                    }
                )
    if returnList != []:
        return returnList
    else:
        raise ParserException(
            parser="FR-COR_IT-SAR.py",
            message=f"No matching AC and DC data found for {zone_key1}->{zone_key2} exchange at {target_datetime}.",
        )


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: str = "FR-COR",
    zone_key2: str = "IT-SAR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    return fetch_data(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        type="exchange",
    )


@refetch_frequency(timedelta(days=2))
def fetch_exchange_forecast(
    zone_key1: str = "FR-COR",
    zone_key2: str = "IT-SAR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    return fetch_data(
        zone_key1=zone_key1,
        zone_key2=zone_key2,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
        type="exchange_forecast",
    )
