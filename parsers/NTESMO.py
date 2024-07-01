"""Parser for AU-NT using https://ntesmo.com.au data, the electricity market operator for the Northen Territories.
Uses some webscrapping as no API seems to be available. Data is available in the form of daily xslx files.
Mapping is done using EDL's website and Territory Generation.
https://edlenergy.com/project/pine-creek/
https://territorygeneration.com.au/about-us/our-power-stations/
"""

import collections
import logging
import math
import re
from collections.abc import Iterable, Iterator
from datetime import date, datetime, time, timedelta, timezone
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
    "RD01": Generator(power_plant="", fuel_type="unknown"),
    "RB01": Generator(power_plant="", fuel_type="unknown"),
    "RB02": Generator(power_plant="", fuel_type="unknown"),
    "RB03": Generator(power_plant="", fuel_type="unknown"),
}

# For some reason the page doesn't always load on first attempt.
# Therefore we retry a few times.
retry_strategy = Retry(
    total=3,
    status_forcelist=[500, 502, 503, 504],
)


def _scan_daily_report_urls(
    urls: Iterable[str], session: Session
) -> Iterator[tuple[date, str]]:
    """Scans pages of daily report cards yielding links to the excel data files for each day."""

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
                timestamp = a.find("div", {"class": "smp-tiles-article__title"}).text

                try:
                    date_time = datetime.strptime(timestamp, "%d %B %Y")
                except ValueError:
                    # some dates are not formatted properly or will contain extra information
                    # e.g. "05 April 2018 - Publishing Recommencement", "05 January 2018 - System Notice", "18 June2018"
                    # so extract individual %d %B %Y groups, potentially separated by 0 or more spaces
                    match = re.search(r"(\d{2})\s*([a-zA-Z]+)\s*(\d{4})", timestamp)
                    if not match:
                        raise
                    cleaned_timestamp = " ".join(match.groups())

                    # some timestamps have typos e.g.  "02 Januray 2019"
                    cleaned_timestamp = cleaned_timestamp.replace("Januray", "January")

                    date_time = datetime.strptime(cleaned_timestamp, "%d %B %Y")

                dt = date_time.replace(tzinfo=AUSTRALIA_TZ).date()
                yield dt, a["href"]


def _find_link_to_daily_report(target_datetime: datetime, session: Session) -> str:
    """Scrapes daily report cards to find the link to the data for the target date."""

    today_datetime = datetime.now(AUSTRALIA_TZ)
    today_date = today_datetime.date()
    target_datetime = target_datetime.astimezone(AUSTRALIA_TZ)
    target_date = target_datetime.date()

    is_this_year = target_date.year == today_date.year
    if is_this_year:
        # current year's report cards are paginated (9 per page) [and in reverse chronological order, latest data first]
        maximum_possible_num_pages = int(math.ceil(365 / 9))
        urls = (
            f"{API_URL}?result_70160_result_page={page_number}"
            # page 0 is a hidden page. Usually it's just a duplicate of page=1, but it seems like sometimes it's
            # updated with new daily data before page 1 is.
            for page_number in range(0, maximum_possible_num_pages + 1)
        )
    else:
        # historical report cards are all on the same page
        urls = [
            f"{API_URL}/historical-daily-trading-data/{target_date.year}-daily-trading-data"
        ]

    index = _scan_daily_report_urls(urls, session=session)

    # cap target date if more recent than what the API makes available:
    # data for a given day is published with a variable delay (+1-4 days)
    if is_this_year:
        date_of_latest_available_data, link = next(index)
        if target_date >= date_of_latest_available_data:
            return link

    for dt, link in index:
        if dt == target_date:
            return link

    raise ParserException(
        PARSER,
        f"Cannot find link to daily report for date {target_date.strftime('%Y-%m-%d %Z')}",
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
    raw_production_mix_df: pd.DataFrame, logger: logging.Logger
) -> list[dict]:
    raw_production_mix_df["Period Start"] = raw_production_mix_df[
        "Period Start"
    ].dt.tz_localize("Australia/Darwin")

    # some older data may miss columns for newer plants
    raw_production_mix_df = raw_production_mix_df.dropna(axis=1, how="all")

    generation_units = set(raw_production_mix_df.columns)
    generation_units.remove("Period Start")
    generation_units.remove("Period End")
    unknown_units = generation_units.difference(PLANT_MAPPING.keys())
    if unknown_units:
        logger.warning(
            f"New generator(s) {unknown_units} detected in {ZONE_KEY}, please update the mapping of generators."
        )

    production_breakdown_list = []
    for row in raw_production_mix_df.itertuples():
        production_mix = collections.defaultdict(float)
        for generator_key in generation_units:
            generator_production = getattr(row, generator_key)

            # Some decommissioned plants have negative production values.
            if generator_production < 0:
                continue

            fuel_type = (
                "unknown"
                if generator_key in unknown_units
                else PLANT_MAPPING[generator_key]["fuel_type"]
            )
            production_mix[fuel_type] += generator_production

        production_breakdown = {
            "zoneKey": ZONE_KEY,
            "datetime": row[1].to_pydatetime(),
            "source": "ntesmo.com.au",
            "production": dict(production_mix),
            "storage": {},
        }
        production_breakdown_list.append(production_breakdown)

    return production_breakdown_list


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
        usecols="A:AE",
        skiprows=4,
        # avoid loading potential extra non-numerical lines at the bottom of the sheet
        # e.g. sometimes there might be a disclaimer
        nrows=48,
    )

    return parse_production_mix(production_mix, logger=logger)


if __name__ == "__main__":
    for dt in [
        # now
        None,
        # this year, but old enough that the api data is not in the first page of results
        datetime(2024, 4, 2, tzinfo=timezone.utc),
        # historical data (previous years)
        datetime(2023, 2, 15, tzinfo=timezone.utc),
        datetime(2022, 3, 11, tzinfo=timezone.utc),
    ]:
        print(f"fetch_consumption(target_datetime={dt}) ->")
        print(fetch_consumption(target_datetime=dt))

        print(f"fetch_price(target_datetime={dt}) ->")
        print(fetch_price(target_datetime=dt))

        print(f"fetch_production(target_datetime={dt}) ->")
        print(fetch_production(target_datetime=dt))
