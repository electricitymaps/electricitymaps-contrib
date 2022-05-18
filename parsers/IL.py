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

import arrow
from bs4 import BeautifulSoup
from requests import get

IEC_URL = "www.iec.co.il"
IEC_PRODUCTION = (
    "https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx"
)
IEC_PRICE = "https://www.iec.co.il/homeclients/pages/tariffs.aspx"
TZ = "Asia/Jerusalem"


def fetch_all() -> list:
    """Fetch info from IEC dashboard."""
    first = get(IEC_PRODUCTION)
    first.cookies
    second = get(IEC_PRODUCTION, cookies=first.cookies)
    soup = BeautifulSoup(second.content, "lxml")

    values: list = soup.find_all("span", class_="statusVal")
    del values[1]

    cleaned_list = []
    for value in values:
        value = re.findall("\d+", value.text.replace(",", ""))
        cleaned_list.append(value)

    def flatten_list(_2d_list) -> list:
        """Flatten the list."""
        flat_list = []
        for element in _2d_list:
            if type(element) is list:
                for item in element:
                    flat_list.append(item)
            else:
                flat_list.append(element)
        return flat_list

    return flatten_list(cleaned_list)


def fetch_price(zone_key="IL", session=None, target_datetime=None, logger=None) -> dict:
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
    date_str = soup.find("span", lang="HE").text
    date_str = date_str.split(sep=" - ")
    date_str = date_str.pop(1)

    date = arrow.get(date_str, "DD.MM.YYYY").datetime

    return date


def fetch_production(
    zone_key="IL", session=None, target_datetime=None, logger=None
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = fetch_all()
    production = [float(item) for item in data]

    # all mapped to unknown as there is no available breakdown
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "production": {"unknown": production[0] + production[1]},
        "source": IEC_URL,
    }


def fetch_consumption(
    zone_key="IL", session=None, target_datetime=None, logger=None
) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = fetch_all()
    consumption = [float(item) for item in data]

    # all mapped to unknown as there is no available breakdown
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
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
