"""Parser that uses the RTE-FRANCE API"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import PriceList
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

PARSER = "GB.py"
TIMEZONE = ZoneInfo("Europe/London")
ZONE_KEY = ZoneKey("GB")


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Returns one-hourly prices for the requested day."""

    now = datetime.now(timezone.utc)
    target_datetime = (
        now if target_datetime is None else target_datetime.astimezone(timezone.utc)
    )

    # API works in UTC timestamps
    day = target_datetime.strftime("%d/%m/%Y")
    url = f"http://eco2mix.rte-france.com/curves/getDonneesMarche?dateDeb={day}&dateFin={day}&mode=NORM"

    session = session or Session()
    response = session.get(url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching price error code: {response.status_code}: {response.text}",
            zone_key,
        )

    xml_tree = ET.fromstring(response.content)

    price_list = PriceList(logger=logger)
    for daily_market_data in xml_tree.iterfind("donneesMarche"):
        day = datetime.strptime(daily_market_data.get("date"), "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        for daily_zone_data in daily_market_data:
            zone_code = daily_zone_data.get("perimetre")

            # Data for Germany / Luxembourg is not set / reported as aggregate region
            if zone_code in {"DE", "DL"}:
                continue

            if zone_key != zone_code:
                continue

            granularity = daily_zone_data.get("granularite")
            if granularity != "Global":
                continue

            for value in daily_zone_data:
                price = None if value.text == "ND" else float(value.text)
                if price is None:
                    continue

                period_number = int(value.attrib["periode"])
                dt = day + timedelta(hours=period_number)
                is_future = dt > now

                price_list.append(
                    zoneKey=zone_key,
                    datetime=dt,
                    source="rte-france.com",
                    price=price,
                    currency="EUR",
                    sourceType=EventSourceType.forecasted
                    if is_future
                    else EventSourceType.measured,
                )

    return price_list.to_list()


if __name__ == "__main__":
    for zone_key in ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]:
        print(f"fetch_price({zone_key}) ->")
        print(fetch_price(ZoneKey(zone_key)))

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    print(f"fetch_price(target_datetime={historical_datetime.isoformat()}) ->")
    print(fetch_price(target_datetime=historical_datetime))
