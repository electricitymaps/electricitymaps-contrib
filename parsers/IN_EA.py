from collections.abc import Callable
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeList
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
HOST = "https://app.erldc.in"
INTERNATIONAL_EXCHANGES_URL = "{proxy}/api/pspreportpsp/Get/pspreport_psp_transnationalexchange/GetByTwoDate?host={host}&firstDate={target_date}&secondDate={target_date}"
INTERREGIONAL_EXCHANGES_URL = "{proxy}/api/pspreportpsp/Get/pspreport_psp_interregionalexchanges/GetByTwoDate?host={host}&firstDate={target_date}&secondDate={target_date}"
IN_EA_TZ = ZoneInfo("Asia/Kolkata")

INTERREGIONAL_EXCHANGES = {
    ZoneKey("IN-EA->IN-NO"): "Import/Export between EAST REGION and NORTH REGION",
    ZoneKey("IN-EA->IN-NE"): "Import/Export between EAST REGION and NORTH_EAST REGION",
    ZoneKey("IN-EA->IN-SO"): "Import/Export between EAST REGION and SOUTH REGION",
    ZoneKey("IN-EA->IN-WE"): "Import/Export between EAST REGION and WEST REGION",
}
INTERRNATIONAL_EXCHANGES = {
    ZoneKey("BT->IN-EA"): "BHUTAN",
    ZoneKey("IN-EA->NP"): "NEPAL",
    ZoneKey("BD->IN-EA"): "BANGLADESH",
}
MAPPING = {
    **INTERREGIONAL_EXCHANGES,
    **INTERRNATIONAL_EXCHANGES,
}


def get_fetch_function(
    exchange_key: ZoneKey,
) -> tuple[str, Callable[[list, ZoneKey, Logger], ExchangeList]]:
    """Get the url, the lookup key and the extract function for the exchange."""
    if exchange_key not in MAPPING:
        raise ParserException(
            "IN_EA.py",
            f"Unsupported exchange key {exchange_key}",
            zone_key=exchange_key,
        )
    if exchange_key in INTERRNATIONAL_EXCHANGES:
        return (
            INTERNATIONAL_EXCHANGES_URL,
            extract_international_exchanges,
        )
    return (
        INTERREGIONAL_EXCHANGES_URL,
        extract_interregional_exchanges,
    )


def extract_international_exchanges(
    raw_data: list, exchange_key: ZoneKey, logger: Logger
) -> ExchangeList:
    exchanges = ExchangeList(logger)
    zone_data = [item for item in raw_data if item["Region"] == MAPPING[exchange_key]][
        0
    ]
    exchanges.append(
        zoneKey=exchange_key,
        datetime=datetime.strptime(zone_data["Date"], "%Y-%m-%d").replace(
            tzinfo=IN_EA_TZ
        ),
        netFlow=float(zone_data["DayAverageMW"]),
        source="erldc.in",
    )
    return exchanges


def extract_interregional_exchanges(
    raw_data: list, exchange_key: ZoneKey, logger: Logger
) -> ExchangeList:
    exchanges = ExchangeList(logger)
    zone_data = [item for item in raw_data if item["Type"] == MAPPING[exchange_key]]
    imports = sum(float(item["ImportMW"]) for item in zone_data)
    exports = sum(float(item["ExportMW"]) for item in zone_data)  # always negative
    exchanges.append(
        zoneKey=exchange_key,
        datetime=datetime.strptime(zone_data[0]["Date"], "%Y-%m-%d").replace(
            tzinfo=IN_EA_TZ
        ),
        netFlow=imports + exports,
        source="erldc.in",
    )
    return exchanges


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """collects average daily exchanges for ERLC"""
    if target_datetime is None:
        # 1 day delay observed
        target_datetime = datetime.now(tz=IN_EA_TZ).replace(
            hour=0, minute=0, second=0
        ) - timedelta(days=1)
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    target_date = target_datetime.strftime("%Y-%m-%d")
    url, extract_function = get_fetch_function(sorted_zone_keys)
    resp = session.get(
        url=url.format(
            proxy=IN_WE_PROXY,
            host=HOST,
            target_date=target_date,
        )
    )
    if not resp.ok:
        raise ParserException(
            parser="IN_EA.py",
            message=f"{target_datetime}: {sorted_zone_keys} data is not available : [{resp.status_code}]",
            zone_key=sorted_zone_keys,
        )
    data = resp.json()
    exchanges = extract_function(data, sorted_zone_keys, logger)
    return exchanges.to_list()
