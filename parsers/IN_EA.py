from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pytz
from requests import Response, Session

from parsers.lib.exceptions import ParserException
from parsers.lib.quality import validate_datapoint_format

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
IN_EA_TZ = pytz.timezone("Asia/Kolkata")
EXCHANGE_MAPPING = {
    "IN-NO": "Import/Export between EAST REGION and NORTH REGION",
    "IN-NE": "Import/Export between EAST REGION and NORTH_EAST REGION",
    "IN-SO": "Import/Export between EAST REGION and SOUTH REGION",
    "IN-WE": "Import/Export between EAST REGION and WEST REGION",
}


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """collects average daily exchanges for ERLC"""
    if target_datetime is None:
        # 1 day delay observed
        target_datetime = arrow.now(tz=IN_EA_TZ).floor("day").datetime - timedelta(
            days=1
        )

    target_date = target_datetime.strftime("%Y-%m-%d")
    url_exchange = f"{IN_WE_PROXY}/api/pspreportpsp/Get/pspreport_psp_interregionalexchanges/GetByTwoDate?host=https://app.erldc.in&firstDate={target_date}&secondDate={target_date}"
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    resp: Response = session.get(url=url_exchange)
    if resp.status_code == 200:
        data = resp.json()
        zone_data = [
            item for item in data if item["Type"] == EXCHANGE_MAPPING[zone_key2]
        ]
        imports = sum(float(item["ImportMW"]) for item in zone_data)
        exports = sum(float(item["ExportMW"]) for item in zone_data)  # always negative
        data_point = {
            "datetime": target_datetime.replace(tzinfo=IN_EA_TZ),
            "sortedZoneKeys": sorted_zone_keys,
            "netFlow": imports + exports,
            "source": "erldc.in",
        }
        validate_datapoint_format(
            datapoint=data_point, zone_key=zone_key1, kind="exchange"
        )
        return data_point
    else:
        raise ParserException(
            parser="IN_EA.py",
            message=f"{target_datetime}: {sorted_zone_keys} data is not available : [{resp.status_code}]",
        )
