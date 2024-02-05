"""
Israel's electricity system load parser.

Source: Israel Electric Corporation
URL: https://www.iec.co.il/en/pages/default.aspx

Shares of Electricity production in 2019:
    64.0% Gas
    31.0% Coal
    1.0% oil,
    4.0% Renewables
    (source: IEA; https://www.iea.org/data-and-statistics?country=ISRAEL&fuel=Electricity%20and%20heat&indicator=Electricity%20generation%20by%20source)
"""

import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import arrow
from bs4 import BeautifulSoup
from requests import Response, Session, get

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

URL = "https://www.noga-iso.co.il/Umbraco/Api/Documents/GetElectricalData"

IEC_URL = "www.iec.co.il"
IEC_PRODUCTION = (
    "https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx"
)
IEC_PRICE = "https://www.iec.co.il/homeclients/pages/tariffs.aspx"
TZ = ZoneInfo("Asia/Jerusalem")


def fetch_all() -> list:
    """Fetch info from IEC dashboard."""
    first = get(IEC_PRODUCTION)
    second = get(IEC_PRODUCTION, cookies=first.cookies)
    soup = BeautifulSoup(second.content, "lxml")

    values: list = soup.find_all("span", class_="statusVal")
    if len(values) == 0:
        raise ValueError("Could not parse IEC dashboard")
    del values[1]

    cleaned_list = []
    for value in values:
        value = re.findall(r"\d+", value.text.replace(",", ""))
        cleaned_list.append(value)

    def flatten_list(_2d_list) -> list:
        """Flatten the list."""
        flat_list = []
        for element in _2d_list:
            if isinstance(element, list):
                for item in element:
                    flat_list.append(item)
            else:
                flat_list.append(element)
        return flat_list

    return flatten_list(cleaned_list)


def fetch_price(
    zone_key: str = "IL",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch price from IEC table."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    with get(IEC_PRICE) as response:
        soup = BeautifulSoup(response.content, "lxml")

    price = soup.find("td", class_="ms-rteTableEvenCol-6")

    return {
        "zoneKey": zone_key,
        "currency": "NIS",
        "datetime": extract_price_date(soup),
        "price": float(price.p.text),
        "source": IEC_URL,
    }


def extract_price_date(soup):
    """Fetch updated price date."""
    span_soup = soup.find("span", lang="HE")
    if span_soup:
        date_str = span_soup.text
    else:
        raise ValueError("Could not parse IEC price date")
    date_str = date_str.split(sep=" - ")
    date_str = date_str.pop(1)

    date = arrow.get(date_str, "DD.MM.YYYY").datetime

    return date


def fetch_noga_iso_data(session: Session, logger: Logger):
    """Fetches data from Noga-ISO"""
    response: Response = session.get(URL)
    if not response.ok:
        logger.warning(
            "IL.py",
            "Failed to fetch data from www.noga-iso.co.il with error: {response.status_code}",
        )

    data = response.json()
    return data


def fetch_production(
    zone_key: ZoneKey = ZoneKey("IL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    session = session or Session()

    data = fetch_noga_iso_data(session, logger)
    eventList = ProductionBreakdownList(logger=logger)

    productionMix = ProductionMix()

    productionMix.add_value(
        mode="unknown", value=float(data.get("Production").replace(",", ""))
    )

    eventList.append(
        zoneKey=zone_key,
        datetime=datetime.now(tz=TZ),
        production=productionMix,
        source="noga-iso.co.il",
    )

    return eventList.to_list()


def fetch_total_production(
    zone_key: ZoneKey = ZoneKey("IL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    session = session or Session()

    data = fetch_noga_iso_data(session, logger)

    eventList = TotalProductionList(logger=logger)

    eventList.append(
        zoneKey=zone_key,
        datetime=datetime.now(tz=TZ),
        value=float(data.get("Production").replace(",", "")),
        source="noga-iso.co.il",
    )


def fetch_consumption(
    zone_key: str = "IL",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = fetch_all()
    consumption = [float(item) for item in data]

    # all mapped to unknown as there is no available breakdown
    return {
        "zoneKey": zone_key,
        "datetime": datetime.now(tz=TZ),
        "consumption": consumption[0],
        "source": IEC_URL,
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_price() ->")
    print(fetch_price())
