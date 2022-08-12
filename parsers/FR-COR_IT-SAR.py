from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional

from requests import Session

from .ENTSOE import fetch_exchange as fetch_ENTSOE_exchange
from .lib.config import refetch_frequency
from .lib.exceptions import ParserException

"""
Fetches data for the FR-COR->IT-SAR exchange by wrapping the ENTSOE parser.
"""


@refetch_frequency(timedelta(days=2))
def fetch_exchange(
    zone_key1: str = "FR-COR",
    zone_key2: str = "IT-SAR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    # IT-SACOAC to IT-SAR
    AC_dataList = fetch_ENTSOE_exchange(
        zone_key1="FR-COR-AC",
        zone_key2="IT-SAR",
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    )
    # IT-SACODC to IT-SAR
    DC_dataList = fetch_ENTSOE_exchange(
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
            message=f"No matching AC and DC data found for {zone_key1}->{zone_key2} exchange.",
        )
