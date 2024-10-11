#!/usr/bin/env python3
import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

# The request library is used to fetch content through HTTP
from bs4 import BeautifulSoup
from requests import Session, get

from parsers import occtonet

TIMEZONE = ZoneInfo("Asia/Tokyo")


def fetch_production(
    zone_key: str = "JP-KY",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict | list:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = {
        "zoneKey": zone_key,
        "datetime": None,
        "production": {
            "biomass": 0,
            "coal": 0,
            "gas": 0,
            "hydro": None,
            "nuclear": None,
            "oil": 0,
            "solar": None,
            "wind": None,
            "geothermal": None,
            "unknown": 0,
        },
        "storage": {},
        "source": "www.kyuden.co.jp",
    }

    # url for consumption and solar
    url = "https://www.kyuden.co.jp/td_power_usages/pc.html"
    r = get(url)
    r.encoding = "utf-8"
    html = r.text
    soup = BeautifulSoup(html, "lxml")

    # get date
    date_div = soup.find("div", class_="puChangeGraph")
    date_str = re.findall(r"(?<=chart/chart)[\d]+(?=.gif)", str(date_div))[0]

    # get hours and minutes
    time_str = soup.find("p", class_="puProgressNow__time").get_text()
    hours = int(re.findall(r"[\d]+(?=時)", time_str)[0])
    minutes = int(re.findall(r"(?<=時)[\d]+(?=分)", time_str)[0])

    # parse datetime
    dt = datetime.strptime(date_str, "%Y%m%d").replace(
        hour=hours, minute=minutes, tzinfo=TIMEZONE
    )
    data["datetime"] = dt

    # consumption
    consumption = soup.find("p", class_="puProgressNow__useAmount").get_text()
    consumption = re.findall(
        r"(?<=使用量\xa0)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?(?=万kW／)",
        consumption,
    )
    consumption = consumption[0].replace(",", "")
    # convert from 万kW to MW (note: '万' is the unit of 10K)
    consumption = float(consumption) * 10

    # solar
    solar = soup.find("td", class_="puProgressSun__num").get_text()
    # convert from 万kW to MW
    solar = float(solar) * 10

    # add two nuclear power plants at Sendai and Genkai
    sendai_url = (
        "http://www.kyuden.co.jp/php/nuclear/sendai/rename.php?"
        "A=s_power.fdat&B=ncp_state.fdat&_=1520532401043"
    )
    genkai_url = (
        "http://www.kyuden.co.jp/php/nuclear/genkai/rename.php?"
        "A=g_power.fdat&B=ncp_state.fdat&_=1520532904073"
    )

    sendai_raw_text = get(sendai_url).text
    genkai_raw_text = get(genkai_url).text

    regex = r"(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*" + r"(?:[eE][-+]?\d+)?(?=&)"
    sendai_values = re.findall(regex, sendai_raw_text)
    genkai_values = re.findall(regex, genkai_raw_text)

    sendai_total = sum(map(float, sendai_values))
    genkai_total = sum(map(float, genkai_values))

    nuclear = sendai_total + genkai_total
    # convert from 万kW to MW
    nuclear *= 10

    # add the exchange JP-CG->JP-KY
    exchanges = occtonet.fetch_exchange("JP-KY", "JP-CG")
    # find the nearest exchanges in time to consumption timestamp
    nearest_exchanges = sorted(
        exchanges, key=lambda exchange: abs(exchange["datetime"] - dt)
    )
    # take the nearest exchange
    exchange = nearest_exchanges[0]
    # check that consumption and exchange timestamps are within a 15 minute window
    if abs(dt - exchange["datetime"]).seconds <= 900:
        generation = consumption - exchange["netFlow"]
        unknown = generation - nuclear - solar
        data["production"]["solar"] = solar
        data["production"]["nuclear"] = nuclear
        data["production"]["unknown"] = unknown

        return data
    else:
        return []


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
