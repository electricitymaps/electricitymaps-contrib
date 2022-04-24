import re

import arrow
from requests import get
from bs4 import BeautifulSoup

EGAT_GENERATION = "https://energy.go.th/index.html"
#EGAT_GENERATION2 = "https://www.sothailand.com/sysgen/egat/"
EGAT_URL = "www.egat.co.th"
MEA_PRICE = "https://www.mea.or.th/en/profile/109/111"
MEA_URL = "www.mea.or.th"
TZ = "Asia/Bangkok"

def fetch_EGAT() -> str:
    """Pull from Min. of Energy for now as I didn't wanted to write a parser for websocket yet"""
    """The website took around 15s to load, unlike the websocket ver."""
    """Consumption = Production + Import(the latter is done separately)"""
    with get(EGAT_GENERATION) as response:
        EGAT_soup = BeautifulSoup(response.content, 'lxml')

    curr_production = EGAT_soup.find_all('p')[6].text.replace(",", "")
    return curr_production

def fetch_price(zone_key="TH", session=None, target_datetime=None, logger=None) -> dict:
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    """Fetch price from MEA table."""
    with get(MEA_PRICE) as response:
        MEA_soup = BeautifulSoup(response.content, 'lxml')

    """'Over 400 kWh (up from 401st)' from Table 1.1"""
    unit_price_table = MEA_soup.find_all('table')[1]
    price = unit_price_table.find_all("td")[19]
    
    return {
        "zoneKey": zone_key,
        "currency": "THB",
        "datetime": arrow.now(TZ).datetime,
        "price": float(price.text)*1000,
        "source": MEA_URL,
    }

def fetch_production(zone_key="TH", session=None, target_datetime=None, logger=None) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    """All mapped to unknown as there is no available breakdown"""
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "production": {"unknown": float(fetch_EGAT())},
        "source": EGAT_URL,
    }

def fetch_consumption(zone_key="TH", session=None, target_datetime=None, logger=None) -> dict:
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    
    """all mapped to unknown as there is no available breakdown"""
    return {
        "zoneKey": zone_key,
        "datetime": arrow.now(TZ).datetime,
        "consumption": {"unknown": float(fetch_EGAT())},
        "source": EGAT_URL,
    }

if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_price() ->")
    print(fetch_price())
