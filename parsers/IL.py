"""
Israel's electricity system load parser.

Source: Noga - The Israel Independent System Operator Ltd.
URL: https://www.noga-iso.co.il/en/

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
from typing import Optional
import base64
import arrow
from requests import Session, get

NOGA_BASE_URL = "https://www.noga-iso.co.il/"
IEC_PRODUCTION = (
    "https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx"
)
NOGA_ELECTRICITY_CONSUMPTION_API = f"{NOGA_BASE_URL}/Umbraco/Api/Documents/GetElectricalData"
IEC_PRICE = "https://iecapi.iec.co.il//api/content/he-IL?pageRoute=content/tariffs/contentpages/businesselectricitytariff"
TZ = "Asia/Jerusalem"


def fetch_all() -> dict:
    """Fetch info from Noga API."""
    with get(NOGA_ELECTRICITY_CONSUMPTION_API) as response:
        data = response.json()
    return data


def fetch_price(
    zone_key: str = "IL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch price from Noga API."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    with get(IEC_PRICE) as response:
        data = response.json()

    components = data.get("components")
    if not components:
        raise ValueError("Could not parse IEC price")
    general_message = components[0].get("text")
    general_message = base64.b64decode(general_message).decode("utf-8")

    date = extract_date_from_string(general_message)

    table = components[1].get('table', [])
    kw_prices = table[-1]
    price_with_VAT = kw_prices[-1].get("value")
    price_with_VAT = base64.b64decode(price_with_VAT).decode("utf-8")

    return {
        "zoneKey": zone_key,
        "currency": "NIS",
        "datetime": date,
        "price": float(price_with_VAT),
        "source": IEC_PRICE,
    }


def extract_date_from_string(general_message: str) -> datetime:
    regexp = r"(\d{2}.\d{2}.\d{4})"
    match = re.search(regexp, general_message)
    if match:
        date_str = match.group(1)
        return datetime.strptime(date_str, "%d.%m.%Y")
    else:
        raise ValueError("Could not parse IEC price date")


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


def fetch_production(
    zone_key: str = "IL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = fetch_all()
    production = data.get("Production")
    reserve = data.get("CurrentReserve")

    if not production or not reserve:
        raise ValueError("Could not parse Noga production")

    production = production.replace(',', '')
    reserve = reserve.replace(',', '')

    production = float(production) + float(reserve)

    # all mapped to unknown as there is no available breakdown
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "production": {"unknown": production},
        "source": NOGA_BASE_URL,
    }


def fetch_consumption(
    zone_key: str = "IL",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = fetch_all()
    consumption = data.get("Production")
    if not consumption:
        raise ValueError("Could not parse Noga consumption")

    consumption = consumption[0]
    consumption.replace(',', '')
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "consumption": {"unknown": float(consumption)},
        "source": NOGA_BASE_URL,
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_price() ->")
    print(fetch_price())
