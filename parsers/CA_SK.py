from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import List, Optional

from pytz import timezone
from requests import Response, Session

from parsers.lib.exceptions import ParserException

TIMEZONE = timezone("America/Regina")

# URLs for the different endpoints.
PRODUCTION_URL = (
    "https://www.saskpower.com/ignitionapi/PowerUseDashboard/GetPowerUseDashboardData"
)
CONSUMPTION_URL = "https://www.saskpower.com/ignitionapi/Content/GetNetLoad"

PRODUCTION_MAPPING = {
    "Hydro": "hydro",
    "Wind": "wind",
    "Solar": "solar",
    "Natural Gas": "gas",
    "Coal": "coal",
    "Other": "unknown",  # This is internal consumption, losses, heat recovery facilities and small independent power producers.
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"


def validate_zone_key(zone_key: str) -> None:
    if zone_key != "CA-SK":
        raise ParserException(
            "CA_SK.py",
            f"CA_SK.py is not designed to parse zone_key: {zone_key}.",
            zone_key,
        )


def validate_no_datetime(target_datetime: Optional[datetime], zone_key) -> None:
    if target_datetime:
        raise ParserException(
            "CA_SK.py",
            "This parser is unable to fetch historical data.",
            zone_key,
        )


def fetch_production(
    zone_key: str = "CA-SK",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    """This parser function will currently return the daily average of the day in question as hourly data.
    This is because the API only returns daily data but the backend expects hourly values.
    This is in order to facilitate the estimation of the hourly values from the daily average.
    """
    # Validate that the zone key is equal to CA-SK.
    validate_zone_key(zone_key)
    # Validate that the target_datetime is None as this parser is unable to fetch historical data.
    validate_no_datetime(target_datetime, zone_key)

    session = session or Session()

    # Set the headers to mimic a user browser as the API will return a 403 if not.
    headers = {"user-agent": USER_AGENT}
    response: Response = session.get(PRODUCTION_URL, headers=headers)

    if not response.ok:
        raise ParserException(
            "CA_SK.py",
            f"Failed to fetch production data. Response Code: {response.status_code}\nError:\n{response.text}",
            zone_key,
        )

    raw_data = response.json()
    # Date is in the format "Jan 01, 2020"
    raw_date = raw_data["SupplyDataText"]
    date = datetime.strptime(raw_date, "%b %d, %Y")
    production_data = {}

    for value in raw_data["PowerCacheData"]["generationByType"]:
        production_data[PRODUCTION_MAPPING[value["type"]]] = value[
            "totalGenerationForType"
        ]

    data_list: List[dict] = []
    # Hack to return hourly data from daily data for the backend as it expects hourly data.
    for hour in range(0, 24):
        data_list.append(
            {
                "zoneKey": zone_key,
                "datetime": date.replace(hour=hour, tzinfo=TIMEZONE),
                "production": production_data,
                "source": "saskpower.com",
            }
        )

    return data_list


def fetch_consumption(
    zone_key: str = "CA-SK",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    # Validate that the zone key is equal to CA-SK.
    validate_zone_key(zone_key)
    # Validate that the target_datetime is None as this parser is unable to fetch historical data.
    validate_no_datetime(target_datetime, zone_key)

    session = session or Session()

    # Set the headers to mimic a user browser as the API will return a 403 if not.
    headers = {"user-agent": USER_AGENT}

    response: Response = session.get(CONSUMPTION_URL, headers=headers)

    if not response.ok:
        raise ParserException(
            "CA_SK.py",
            f"Failed to fetch consumption data. Response Code: {response.status_code}\nError:\n{response.text}",
            zone_key,
        )

    raw_data = response.json()

    now = datetime.now(TIMEZONE)

    # Data is updated every 5 minutes so we assume the data is from a multiple of 5 minutes and has a 5 minute delay from that multiple.
    assumed_datetime = now.replace(second=0, microsecond=0) - timedelta(
        minutes=(now.minute % 5) + 5
    )

    return [
        {
            "zoneKey": zone_key,
            "datetime": assumed_datetime,
            "consumption": int(raw_data),
            "source": "saskpower.com",
        }
    ]
