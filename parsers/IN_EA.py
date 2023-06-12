from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Dict, List, Optional

import arrow
import pytz
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ExchangeList
from parsers.lib.exceptions import ParserException

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
) -> List[Dict]:
    """collects average daily exchanges for ERLC"""
    if target_datetime is None:
        # 1 day delay observed
        target_datetime = arrow.now(tz=IN_EA_TZ).floor("day").datetime - timedelta(
            days=1
        )

    target_date = target_datetime.strftime("%Y-%m-%d")
    url_exchange = f"{IN_WE_PROXY}/api/pspreportpsp/Get/pspreport_psp_interregionalexchanges/GetByTwoDate?host=https://app.erldc.in&firstDate={target_date}&secondDate={target_date}"
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    exchanges = ExchangeList(logger)
    resp: Response = session.get(url=url_exchange)
    if not resp.ok:
        raise ParserException(
            parser="IN_EA.py",
            message=f"{target_datetime}: {sorted_zone_keys} data is not available : [{resp.status_code}]",
        )
    data = resp.json()
    zone_data = [item for item in data if item["Type"] == EXCHANGE_MAPPING[zone_key2]]
    imports = sum(float(item["ImportMW"]) for item in zone_data)
    exports = sum(float(item["ExportMW"]) for item in zone_data)  # always negative
    exchanges.append(
        sorted_zone_keys=sorted_zone_keys,
        datetime=target_datetime.replace(tzinfo=IN_EA_TZ),
        netFlow=imports + exports,
        source="erldc.in",
    )
    return exchanges.to_list()
