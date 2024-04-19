"""Parser for AU-NT using https://ntesmo.com.au data, the electricity market operator for the Northen Territories.
Uses some webscrapping as no API seems to be available. Data is available in the form of daily xslx files.
Mapping is done using EDL's website and Territory Generation.
https://edlenergy.com/project/pine-creek/
https://territorygeneration.com.au/about-us/our-power-stations/
"""

import math
from datetime import datetime, time, timedelta, timezone
from logging import Logger, getLogger
from typing import TypedDict
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session
from requests.adapters import Retry

from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency, retry_policy
from parsers.lib.exceptions import ParserException

PARSER = "NTESMO.py"
AUSTRALIA_TZ = ZoneInfo("Australia/Darwin")
ZONE_KEY = ZoneKey("AU-NT")

API_URL = "https://ntesmo.com.au/data/daily-trading"


class Generator(TypedDict):
    power_plant: str
    fuel_type: str


PLANT_MAPPING = {
    "C1": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C2": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C3": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C4": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C5": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C6": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C7": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C8": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "C9": Generator(power_plant="Channel Island Power Station", fuel_type="gas"),
    "W1": Generator(power_plant="Weddell Power Station", fuel_type="gas"),
    "W2": Generator(power_plant="Weddell Power Station", fuel_type="gas"),
    "W3": Generator(power_plant="Weddell Power Station", fuel_type="gas"),
    "LMS": Generator(
        power_plant="LMS Energy from the Shoal Bay landfill", fuel_type="biomass"
    ),
    "K1": Generator(power_plant="Katherine Power Station", fuel_type="gas"),
    "K2": Generator(power_plant="Katherine Power Station", fuel_type="gas"),
    "K3": Generator(power_plant="Katherine Power Station", fuel_type="gas"),
    "K4": Generator(power_plant="Katherine Power Station", fuel_type="gas"),
    "P1": Generator(power_plant="Pine Creek Power Station", fuel_type="gas"),
    "P2": Generator(power_plant="Pine Creek Power Station", fuel_type="gas"),
    "P3": Generator(power_plant="Pine Creek Power Station", fuel_type="gas"),
    "KS01": Generator(power_plant="", fuel_type="unknown"),
    "MY01": Generator(power_plant="", fuel_type="unknown"),
    "BJ01": Generator(power_plant="", fuel_type="unknown"),
    "BP01": Generator(power_plant="", fuel_type="unknown"),
    "HP01": Generator(power_plant="", fuel_type="unknown"),
}

# For some reason the page doesn't always load on first attempt.
# Therefore we retry a few times.
retry_strategy = Retry(
    total=3,
    status_forcelist=[500, 502, 503, 504],
)


def _find_link_to_daily_report(target_datetime: datetime, session: Session) -> str:
    """Scrapes daily report cards to find the link to the data for the target date."""

    today_date = datetime.now(AUSTRALIA_TZ).date()
    target_datetime = target_datetime.astimezone(AUSTRALIA_TZ)

    # cap target datetime if more recent that what the API makes available:
    # data is being published after 2 days at the moment
    _DELAY_IN_DAYS = 2
    if abs(today_date - target_datetime.date()).days < _DELAY_IN_DAYS:
        target_datetime = target_datetime - timedelta(days=_DELAY_IN_DAYS)

    this_year = target_datetime.year == today_date.year
    if this_year:
        # current year's report cards are paginated (9 per page)
        num_pages = int(math.ceil(365 / 9))
        urls = (
            f"{API_URL}?result_70160_result_page={page_number}"
            for page_number in range(1, num_pages + 1)
        )
    else:
        # historical report cards are all on the same page
        urls = [
            f"{API_URL}/historical-daily-trading-data/{target_datetime.year}-daily-trading-data"
        ]

    for url in urls:
        response = session.get(url)
        if not response.ok:
            raise ParserException(
                PARSER,
                f"Exception when fetching daily trading data error code: {response.status_code}: {response.text}",
            )

        page = response.text
        soup = BeautifulSoup(page, "html.parser")
        for a in soup.find_all("a", href=True):
            if a["href"].startswith("https://ntesmo.com.au/__data/assets/excel_doc/"):
                dt = a.find("div", {"class": "smp-tiles-article__title"}).text
                if dt == target_datetime.strftime("%d %B %Y"):
                    return a["href"]

    raise ParserException(
        PARSER,
        f"Cannot find link to daily report for date {target_datetime}",
    )


def get_daily_report_data(
    zone_key: ZoneKey,
    session: Session | None,
    target_datetime: datetime,
) -> bytes:
    session = session or Session()

    link_to_daily_report = _find_link_to_daily_report(
        target_datetime=target_datetime, session=session
    )

    response = session.get(link_to_daily_report)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching daily report data error code: {response.status_code}: {response.text}",
            zone_key,
        )

    return response.content


def extract_consumption_and_price_data(file: bytes) -> pd.DataFrame:
    return pd.read_excel(
        file, "System Demand and Market Price", skiprows=4, header=0, usecols="A:C"
    )


def parse_consumption_and_price(
    raw_consumption: pd.DataFrame,
    target_datetime: datetime,
    price: bool,
) -> list[dict]:
    target_datetime = target_datetime.astimezone(AUSTRALIA_TZ)

    data_points = []
    for _, consumption in raw_consumption.iterrows():
        # Market day starts at 4:30 and reports up until 4:00 the next day.
        # Therefore timestamps between 0:00 and 4:30 excluded need to have an extra day.
        raw_timestamp = consumption[0]
        timestamp = datetime.combine(date=target_datetime.date(), time=raw_timestamp)
        if raw_timestamp < time(hour=4, minute=30):
            timestamp = timestamp + timedelta(days=1)
        data_point = {
            "zoneKey": "AU-NT",
            "datetime": timestamp.replace(tzinfo=AUSTRALIA_TZ),
            "source": "ntesmo.com.au",
        }
        if price:
            data_point["price"] = consumption["Market Price"]
            data_point["currency"] = "AUD"
        else:
            data_point["consumption"] = consumption["Demand"]
        data_points.append(data_point)
    return data_points


def parse_production_mix(
    raw_production_mix: pd.DataFrame, logger: Logger
) -> list[dict]:
    production_mix = []
    generation_units = set(raw_production_mix.columns)
    generation_units.remove("Period Start")
    generation_units.remove("Period End")
    if not generation_units == PLANT_MAPPING.keys():
        raise ParserException(
            "NTESMO.py",
            f"New generator {generation_units - PLANT_MAPPING.keys()} detected in AU-NT, please update the mapping of generators.",
        )
    raw_production_mix["Period Start"] = raw_production_mix[
        "Period Start"
    ].dt.tz_localize("Australia/Darwin")
    for _, production in raw_production_mix.iterrows():
        data_point = {
            "zoneKey": "AU-NT",
            "datetime": production["Period Start"].to_pydatetime(),
            "source": "ntesmo.com.au",
            "production": {},
            "storage": {},
        }
        for generator_key, generator in PLANT_MAPPING.items():
            if generator_key not in production:
                raise ParserException(
                    "NTESMO.py",
                    f"Missing generator {generator_key} detected in AU-NT, please update the mapping of generators.",
                )
            # Some decomissioned plants have negative production values.
            if production[generator_key] >= 0:
                if generator["fuel_type"] in data_point["production"]:
                    data_point["production"][generator["fuel_type"]] += production[
                        generator_key
                    ]
                else:
                    data_point["production"][generator["fuel_type"]] = production[
                        generator_key
                    ]
        production_mix.append(data_point)
    return production_mix


@refetch_frequency(timedelta(days=1))
@retry_policy(retry_policy=retry_strategy)
def fetch_consumption(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    daily_report_data = get_daily_report_data(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
    )

    consumption_and_price_data = extract_consumption_and_price_data(daily_report_data)
    return parse_consumption_and_price(
        raw_consumption=consumption_and_price_data,
        target_datetime=target_datetime,
        price=False,
    )


@refetch_frequency(timedelta(days=1))
@retry_policy(retry_policy=retry_strategy)
def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    daily_report_data = get_daily_report_data(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
    )

    consumption_and_price_data = extract_consumption_and_price_data(daily_report_data)
    return parse_consumption_and_price(
        raw_consumption=consumption_and_price_data,
        target_datetime=target_datetime,
        price=True,
    )


@refetch_frequency(timedelta(days=1))
@retry_policy(retry_policy=retry_strategy)
def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    target_datetime = (
        datetime.now(timezone.utc)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )
    daily_report_data = get_daily_report_data(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
    )

    production_mix = pd.read_excel(
        daily_report_data,
        sheet_name="Generating Unit Output",
        header=0,
        usecols="A:AA",
        skiprows=4,
        # avoid loading potential extra non-numerical lines at the bottom of the sheet
        # e.g. sometimes there might be a disclaimer
        nrows=48,
    )
    return parse_production_mix(production_mix, logger)


if __name__ == "__main__":
    for dt in [
        # now
        None,
        # this year, but old enough that the api data is not in the first page of results
        datetime(2024, 4, 2, tzinfo=timezone.utc),
        # historical data (previous years)
        datetime(2023, 2, 15, tzinfo=timezone.utc),
    ]:
        print(f"fetch_consumption(target_datetime={dt}) ->")
        print(fetch_consumption(target_datetime=dt))

        print(f"fetch_price(target_datetime={dt}) ->")
        print(fetch_price(target_datetime=dt))

        print(f"fetch_production(target_datetime={dt}) ->")
        print(fetch_production(target_datetime=dt))
