import re
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import List, NamedTuple, Optional, Union

import arrow
import demjson3 as demjson
import pandas as pd
from bs4 import BeautifulSoup
from dateutil import parser, tz
from requests import Response, Session
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

MOT_URL = "https://www.iemop.ph/market-data/regional-merit-order-table-mot-files/"
TIMEZONE = "Asia/Manila"

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")


class MarketReportsItem(NamedTuple):
    datetime: datetime
    filename: str
    link: str


def get_all_market_reports_items(logger: Logger) -> List[MarketReportsItem]:
    MARKET_REPORT_DIV_CLASS = "market-reports-item"
    MARKET_REPORT_TITLE_CLASS = "market-reports-title"
    title_pattern = re.compile(r".*mot_files_(?P<date>[0-9]*).zip.*")

    logger.debug("Fetching list of market report urls")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(MOT_URL)
    driver.implicitly_wait(3)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    market_report_divs = soup.find_all("div", class_=MARKET_REPORT_DIV_CLASS)

    logger.debug("Succesfully recovered market report items")

    all_items = []
    for market_report_div in market_report_divs:
        market_report_link = market_report_div.find("a")
        market_report_href = market_report_link["href"]

        market_report_txt = market_report_div.find(
            "div", class_=MARKET_REPORT_TITLE_CLASS
        ).text
        date = title_pattern.match(market_report_txt).group("date")
        market_report_filename = f"mot_files_{date}.zip"
        dt = arrow.get(
            date,
            "YYYYMMDD",
            tzinfo=TIMEZONE,
        ).datetime
        all_items.append(
            MarketReportsItem(
                datetime=dt,
                filename=market_report_filename,
                link=MOT_URL + market_report_href,
            )
        )

    driver.quit()

    all_dates = [x.datetime for x in all_items]
    logger.info(
        f"Recovered {len(all_items)} market report items between the {min(all_dates)} and the {max(all_dates)}"
    )

    return all_items


def download_market_reports(
    session: Session, reports_item: MarketReportsItem, logger: Logger
) -> pd.DataFrame:
    dt_extractor = re.compile(r".*_(?P<datetime>[0-9]*).csv")
    res: Response = session.get(reports_item.link)
    from io import BytesIO
    from zipfile import ZipFile

    START_DELIMITER = "********** Offers Dispatched **********"

    logger.debug(f"Downloading market reports for {reports_item.filename}")
    # zip containing a list of csv files which we want to concatenate in a single dataframe
    _all_df = []
    with ZipFile(BytesIO(res.content)) as zip_file:
        for csv_filename in zip_file.namelist():
            if csv_filename.endswith(".csv"):
                with zip_file.open(csv_filename) as csv_file:
                    dt = arrow.get(
                        dt_extractor.match(csv_filename).group("datetime"),
                        "YYYYMMDDHHmmss",
                        tzinfo=TIMEZONE,
                    ).datetime
                    _df = pd.read_csv(csv_file, header=1)
                    # Find index of START_DELIMITER and only keep rows after that
                    start_idx = _df.index[_df["Resource ID"] == START_DELIMITER][0]
                    _df = _df.iloc[start_idx + 1 : -1]
                    # All numeric types
                    _df = _df.apply(pd.to_numeric, errors="ignore")
                    # Add datetime column
                    _df["datetime"] = dt
                    _all_df.append(_df)

    df = pd.concat(_all_df, ignore_index=True)

    logger.info(
        f"Succesfully extracted unit level production between the {df.datetime.min()} and the {df.datetime.max()}"
    )

    return df


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = "PH-LZ",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    reports_items = get_all_market_reports_items(logger)

    # Date filtering - one report item per day
    if target_datetime is None:
        reports_item = reports_items[
            0
        ]  # reports are delayed by a few days, take the most recent
    else:
        try:
            reports_item = next(
                filter(
                    lambda x: x.datetime.date() == target_datetime.date(), reports_items
                )
            )
        except StopIteration:
            logger.warning(
                f"No market report found for {target_datetime.date()} in {zone_key}"
            )
            return []

    df = download_market_reports(session, reports_item, logger)
    # ...
    # TODO map power plant names to mode and zone
    breakpoint()

    return


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    pass


if __name__ == "__main__":
    print(fetch_production())
