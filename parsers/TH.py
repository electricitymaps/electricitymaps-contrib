import re

import arrow
from requests import get
from bs4 import BeautifulSoup

MEA_PRICE = "https://www.mea.or.th/en/profile/109/111"
MEA_URL = "www.mea.or.th/en/home"
TZ = "Asia/Bangkok"

def fetch_price(zone_key="TH", session=None, target_datetime=None, logger=None) -> dict:
    """Fetch price from MEA table."""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    with get(MEA_PRICE) as response:
        soup = BeautifulSoup(response.content, 'lxml')

    """'Over 400 kWh (up from 401st)' from Table 1.1"""
    unit_price_table = soup.find_all('table')[1]
    price = unit_price_table.find_all("td")[19]

    return {
        "zoneKey": zone_key,
        "currency": "THB",
        "datetime": arrow.now(TZ).datetime,
        "price": float(price.text),
        "source": MEA_URL,
    }

if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_price() ->")
    print(fetch_price())
