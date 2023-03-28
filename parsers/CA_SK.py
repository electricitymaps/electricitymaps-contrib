from datetime import datetime
from logging import Logger, getLogger
from typing import List, Optional

from pytz import timezone
from requests import Session

from parsers.lib.exceptions import ParserException

TIMEZONE = timezone("America/Regina")

PRODUCTION_URL = (
    "https://www.saskpower.com/ignitionapi/PowerUseDashboard/GetPowerUseDashboardData"
)

PRODUCTION_MAPPING = {
    "Hydro": "hydro",
    "Wind": "wind",
    "Solar": "solar",
    "Natural Gas": "gas",
    "Coal": "coal",
    "Other": "unknown",  # This is internal consumption and losses.
}




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

    session = session or Session()

    if target_datetime:
        raise ParserException(
            "CA_SK.py", "This parser is unable to fetch historical data.", zone_key
        )

    # Set the headers to mimic a user browser as the API will return a 403 if not.
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36"
    }
    response = session.get(PRODUCTION_URL, headers=headers)

    if not response.ok:
        raise ParserException("CA_SK.py", "Failed to fetch production data.", zone_key)
    rawData = response.json()
    # Date is in the format "Jan 01, 2020"
    rawDate = rawData["SupplyDataText"]
    date = datetime.strptime(rawDate, "%b %d, %Y")
    productionData = {}

    for value in rawData["PowerCacheData"]["generationByType"]:
        productionData[PRODUCTION_MAPPING[value["type"]]] = value[
            "totalGenerationForType"
        ]

    dataList: List[dict] = []
    # Hack to return hourly data from daily data for the backend as it expects hourly data.
    for hour in range(0, 24):
        dataList.append(
            {
                "zoneKey": zone_key,
                "datetime": date.replace(hour=hour, tzinfo=TIMEZONE),
                "production": productionData,
                "source": "saskpower.com",
            }
        )

    return dataList
