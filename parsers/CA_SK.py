from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("America/Regina")
PRODUCTION_URL = (
    "https://www.saskpower.com/ignitionapi/PowerUseDashboard"
    "/GetPowerUseDashboardData"
)
CONSUMPTION_URL = "https://www.saskpower.com/ignitionapi/Content/GetNetLoad"
PRODUCTION_MAPPING = {
    "Hydro": "hydro",
    "Wind": "wind",
    "Solar": "solar",
    "Natural Gas": "gas",
    "Coal": "coal",
    # "Other" represents internal consumption, losses, heat recovery facilities
    # and small independent power producers.
    "Other": "unknown",
}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
)


def _request(
    session: Session | None,
    target_datetime: datetime | None,
    url: str,
    zone_key: ZoneKey,
) -> dict | str:
    # The source does not offer historical data, so bail out if it's requested.
    if target_datetime:
        raise ParserException("CA_SK.py", "Unable to fetch historical data", zone_key)
    # The zone key must be "CA-SK"; bail out otherwise.
    if zone_key != "CA-SK":
        raise ParserException("CA_SK.py", f"Cannot parse zone '{zone_key}'", zone_key)
    session = session or Session()
    # Mimic a user browser in the headers or the API will respond with a 403.
    response = session.get(url, headers={"user-agent": USER_AGENT})
    if not response.ok:
        raise ParserException(
            "CA_SK.py",
            f"Request to {url} failed. Response Code: {response.status_code}\n"
            f"Error:\n{response.text}",
            zone_key,
        )
    return response.json()


def fetch_production(
    zone_key: ZoneKey = ZoneKey("CA-SK"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    payload = _request(session, target_datetime, PRODUCTION_URL, zone_key)
    if not isinstance(payload, dict):
        raise ParserException("CA_SK.py", "Unexpected payload type", zone_key)
    # Date is in the format "Jan 01, 2020"
    date = datetime.strptime(payload["SupplyDataText"], "%b %d, %Y")
    production_mix = ProductionMix()
    for generation_by_type in payload["PowerCacheData"]["generationByType"]:
        production_mix.add_value(
            PRODUCTION_MAPPING[generation_by_type["type"]],
            generation_by_type["totalGenerationForType"],
        )
    production_breakdown_list = ProductionBreakdownList(logger)
    # Copy the daily average returned by the API into hourly values. This is a
    # bit of a hack, but it's required because the back-end requires hourly
    # datapoints while the API only provides daily averages.
    for hour in range(24):
        production_breakdown_list.append(
            datetime=date.replace(hour=hour, tzinfo=TIMEZONE),
            production=production_mix,
            source="saskpower.com",
            zoneKey=ZoneKey(zone_key),
        )
    return production_breakdown_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("CA-SK"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    payload = _request(session, target_datetime, CONSUMPTION_URL, zone_key)
    if not isinstance(payload, str):
        raise ParserException("CA_SK.py", "Unexpected payload type", zone_key)
    # The source refreshes every 5 minutes, so we assume the current data is
    # from 5 minutes before the most recent multiple of 5 minutes.
    now = datetime.now(TIMEZONE)
    assumed_datetime = now.replace(second=0, microsecond=0) - timedelta(
        minutes=(5 + now.minute % 5)
    )
    total_consumption = TotalConsumptionList(logger)
    total_consumption.append(
        consumption=float(payload),
        datetime=assumed_datetime,
        source="saskpower.com",
        zoneKey=zone_key,
    )
    return total_consumption.to_list()
