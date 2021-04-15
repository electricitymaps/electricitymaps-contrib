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
from requests import get
from bs4 import BeautifulSoup

IEC_URL = "www.iec.co.il"
IEC_PRODUCTION = (
    "https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx"
)
PRICE = "50.66"  # Price is determined yearly
TZ = "Asia/Jerusalem"


def flatten_list(_2d_list) -> list:
    flat_list = []
    for element in _2d_list:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list


def fetch_production(zone_key="IL", session=None, logger=None) -> dict:
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

    cleaned_list = flatten_list(cleaned_list)

    production = [float(item) for item in cleaned_list]

    # all mapped to unknown as there is no available breakdown
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "production": {
            "unknown": production[0] + production[1]
        },
        "source": IEC_URL,
        "price": PRICE,
    }


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
