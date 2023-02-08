#!/usr/bin/env python3

from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

from bs4 import BeautifulSoup
from pytz import timezone
from requests import Session

#   MAIN_WEBSITE = https://ndc.energy.mn/
NDC_GENERATION = "https://disnews.energy.mn/test/convert.php"
TZ = "Asia/Ulaanbaatar"  # UTC+8


def fetch_production(
    zone_key: str = "MN",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")
    with session.get(NDC_GENERATION) as response:
        NDC_SOUP = BeautifulSoup(response.content, "html.parser")

    # Нийлбэр ачаалал / total load/demand
    consumption_MW = float(NDC_SOUP.find_all("td")[6].text.strip(" МВт"))
    # НЦС / Нарны Цахилгаан Станц # Yes, solar DOES produce at night (!) because of the use of thermal-based Concentrated Solar Power / CSP
    solar_MW = float(NDC_SOUP.find_all("td")[7].text.strip(" МВт"))
    # СЦС / Салхин Цахилгаан Станц # wind energy
    wind_MW = float(NDC_SOUP.find_all("td")[8].text.strip(" МВт"))
    # Импортын чадал # exchange balance - positive=import; negative=export
    exchanges_MW = float(NDC_SOUP.find_all("td")[9].text.strip(" МВт"))
    # Calculated 'unknown' production from the 4 values above.
    # 'unknown' consists of 92.8% coal, 5.8% oil and 1.4% hydro as per 2020; sources: IEA and IRENA statistics.
    unknown_MW = round(consumption_MW - exchanges_MW - solar_MW - wind_MW, 2)

    dataset_production = {"unknown": unknown_MW, "solar": solar_MW, "wind": wind_MW}

    date_raw = NDC_SOUP.find_all("td")[0].text.strip("Хоногийн ачаалал: ")
    date_pretty = datetime.strptime(date_raw, "%Y-%m-%d")
    time_raw = NDC_SOUP.find_all("td")[14].text.strip("Импортын чадал ")
    time_time = datetime.strptime(time_raw, "%H:%M:%S")
    time_pretty = datetime.time(time_time)

    time_combined = datetime.combine(date_pretty, time_pretty)

    data = {
        "zoneKey": zone_key,
        "datetime": time_combined.replace(tzinfo=timezone(TZ)),
        "production": dataset_production,
        "source": "https://ndc.energy.mn/",
    }

    return data


def fetch_consumption(
    zone_key: str = "MN",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")
    with session.get(NDC_GENERATION) as response:
        NDC_SOUP = BeautifulSoup(response.content, "html.parser")

    # Нийлбэр ачаалал
    consumption_MW = float(NDC_SOUP.find_all("td")[6].text.strip(" МВт"))

    date_raw = NDC_SOUP.find_all("td")[0].text.strip("Хоногийн ачаалал: ")
    date_pretty = datetime.strptime(date_raw, "%Y-%m-%d")
    time_raw = NDC_SOUP.find_all("td")[14].text.strip("Импортын чадал ")
    time_time = datetime.strptime(time_raw, "%H:%M:%S")
    time_pretty = datetime.time(time_time)

    time_combined = datetime.combine(date_pretty, time_pretty)

    data = {
        "zoneKey": zone_key,
        "datetime": time_combined.replace(tzinfo=timezone(TZ)),
        "consumption": consumption_MW,
        "source": "https://ndc.energy.mn/",
    }

    return data


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
