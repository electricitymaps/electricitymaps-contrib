#!/usr/bin/env python3

import csv
from datetime import date, datetime, timedelta
from io import StringIO
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

TIMEZONE = ZoneInfo("Asia/Singapore")

# "Metered Generation by Facility Type" from the data downloads on https://www.nems.emcsg.com/nems-prices:
# half-hourly settlement data, published about 2 weeks late, back to 2020. The empty
# `seriesName` and `tpcValue` are required, without them the site answers with a 404 page.
DATA_DOWNLOAD_URL = "https://www.nems.emcsg.com/api/sitecore/DataSync/DataDownload"
METERED_GENERATION = 16
MAX_DOWNLOAD_DAYS = 30  # the site's limit on a download's date range

# Backend of the charts on https://www.home.emcsg.com/. Given a `fromDate`, each
# dataset covers the 7 days before it. History goes back to 2024.
DATASYNC_URL = "https://www.home.emcsg.com/api/DataSync/Get"
HALF_HOURLY_PRICE_DEMAND = 14  # half-hourly USEP ($/MWh) and demand (MW)

SOURCE = "emcsg.com"

"""
Around 95% of Singapore's generation is done with combined-cycle gas turbines.

Resources:

- https://www.ema.gov.sg/Statistics.aspx particularly filtering by "Generation"
The most recent document at time of writing is
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Statistics/27RSU.pdf
It says that between January 2016 and March 2017, non-gas monthly generation breakdown has been 0.7% to 1.4% coal,
0.1% to 1.0% "petroleum products" (excluding an exceptional value of 3.9% in Nov 2016),
and 2.7% to 3.4% "other", which includes among others waste-to-energy and solar.

- Write-up of energy statistics in 2015 and first half of 2016:
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Publications/SES/2016/Singapore%20Energy%20Statistics%202016.pdf
(referred to as "Singapore Energy Statistics 2016" below)
It states among others "In 2015, [natural gas] accounted for about 95% of fuel mix,
comparable with that recorded in 2014. Petroleum products, mainly in the form of diesel and fuel oil,
made up 0.7% of the fuel mix. Other energy products (e.g. municipal waste, coal and biomass)
accounted for 2.9% while the remaining 1.2% was from coal", and that steam turbines in Singapore
"typically run on fuel oil and diesel'

EMC publishes metered generation for the facility types "CCGT/COGEN/TRIGEN", "GT", "ST", "IGS",
"OTHERS", "ESS" (called "BATTERY" before 2026) and "IMPORT". I take the first three to mean combined-cycle
gas turbines/co-generation/tri-generation, single-cycle gas turbines (following the Energy Statistics 2016
pg 24), and steam turbines respectively. There is no information on fuel for steam turbines. IGS are
intermittent generation sources, i.e. solar.

For Electricity Map, we map CCGT and GT to gas, ST and OTHERS to "unknown", IGS to solar and ESS
(energy storage systems) to battery. IMPORT is left out: imports are not production, and the
interconnection to Malaysia is implemented in MY_WM.py.

Metered generation comes about 2 weeks late, and EMC publishes nothing more recent that is both
half-hourly and complete: its charts only have daily shares per facility type, without solar.
"""

FACILITY_TYPE_MAPPINGS = {
    "CCGT/COGEN/TRIGEN": "gas",
    "GT": "gas",
    "ST": "unknown",
    "IGS": "solar",
    "OTHERS": "unknown",
}
STORAGE_FACILITY_TYPES = {"ESS", "BATTERY"}


def _fetch_metered_generation(session: Session, end: date) -> list[dict[str, str]]:
    """Returns the CSV rows of the 30 days up to `end` included."""
    start = end - timedelta(days=MAX_DOWNLOAD_DAYS - 1)
    response = session.get(
        DATA_DOWNLOAD_URL,
        params={
            "value": METERED_GENERATION,
            "fromDate": start.isoformat(),
            "toDate": end.isoformat(),
            "seriesName": "",
            "tpcValue": 1,
        },
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    if response.status_code == 204:
        raise ParserException(
            "SG.py",
            f"No metered generation published between {start} and {end}",
            ZoneKey("SG"),
        )
    return list(csv.DictReader(StringIO(response.text)))


def _fetch_datasets(
    session: Session, value: int, end: date
) -> tuple[list[str], dict[str, list[str]]]:
    """Returns the labels and datasets (label -> values) of the 7 days up to `end` included."""
    from_date = (end + timedelta(days=1)).isoformat()
    response = session.get(
        DATASYNC_URL,
        params={"value": value, "fromDate": from_date, "toDate": from_date},
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()
    blocks = response.json()["data"]["data"]
    if not blocks:
        raise ParserException("SG.py", f"No data from EMC up to {end}", ZoneKey("SG"))
    return blocks[0]["labels"], {
        dataset["label"]: dataset["data"] for dataset in blocks[0]["datasets"]
    }


def _parse_label(label: str, end: date) -> datetime:
    """Turns labels like "03 Nov 00:00-00:30" into the (period start) datetime.

    Labels have no year, so we take the one that puts the label on or before `end`.
    """
    period_start = label.split("-")[0]
    dt = datetime.strptime(f"{end.year} {period_start}", "%Y %d %b %H:%M")
    if dt.date() > end:
        dt = dt.replace(year=end.year - 1)
    return dt.replace(tzinfo=TIMEZONE)


def _end_date(target_datetime: datetime | None) -> date:
    """The last day to fetch: the target day, or yesterday as today isn't published yet."""
    if target_datetime is None:
        return datetime.now(tz=TIMEZONE).date() - timedelta(days=1)
    return target_datetime.astimezone(TIMEZONE).date()


@refetch_frequency(timedelta(days=MAX_DOWNLOAD_DAYS))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("SG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Requests the half-hourly metered production mix (in MW) of Singapore over 30 days.

    Live, that is the last ~2 weeks published, as metering data comes about 2 weeks late.
    """
    rows = _fetch_metered_generation(session or Session(), _end_date(target_datetime))
    known_types = {*FACILITY_TYPE_MAPPINGS, *STORAGE_FACILITY_TYPES, "IMPORT"}
    for facility_type in {row["FACILITY TYPE"] for row in rows} - known_types:
        logger.warning(f'Singapore has unrecognized facility type "{facility_type}"')

    mixes: dict[datetime, tuple[ProductionMix, StorageMix]] = {}
    for row in rows:
        dt = datetime.strptime(row["DATE"], "%d-%b-%Y").replace(
            tzinfo=TIMEZONE
        ) + timedelta(minutes=30 * (int(row["PERIOD"]) - 1))
        mix, storage = mixes.setdefault(dt, (ProductionMix(), StorageMix()))
        facility_type = row["FACILITY TYPE"]
        # Energy over a half-hour period, in MWh. Gross is before the facility's own consumption.
        mw = 2 * float(row["GROSS INJECTION (MWh)"])
        if facility_type in STORAGE_FACILITY_TYPES:
            # Injection is discharge, storage is positive when charging.
            storage.add_value("battery", -mw)
        elif facility_type != "IMPORT":
            # Idle units draw a little power, which shows as a small negative injection.
            mix.add_value(
                FACILITY_TYPE_MAPPINGS.get(facility_type, "unknown"),
                mw,
                correct_negative_with_zero=True,
            )

    production_breakdowns = ProductionBreakdownList(logger)
    for dt, (mix, storage) in sorted(mixes.items()):
        production_breakdowns.append(
            datetime=dt,
            zoneKey=zone_key,
            production=mix,
            storage=storage,
            source=SOURCE,
        )
    return production_breakdowns.to_list()


@refetch_frequency(timedelta(days=7))
def fetch_price(
    zone_key: ZoneKey = ZoneKey("SG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Requests the half-hourly power prices in Singapore (USEP) for the past week.

    See https://www.nems.emcsg.com/Guide-To-Prices for details of what different prices in the data source mean.
    We use USEP here: "The Uniform Singapore Energy Price (USEP) is the uniform price of energy
    that applies for settlement purposes for all energy injections or withdrawals that are deemed to occur
    at the Singapore hub. It is the weighted-average of the nodal prices at all off-take nodes in each half hour."
    """
    end = _end_date(target_datetime)
    periods, datasets = _fetch_datasets(
        session or Session(), HALF_HOURLY_PRICE_DEMAND, end
    )

    price_list = PriceList(logger)
    for period, price in zip(periods, datasets["USEP"], strict=True):
        if price is None:
            continue
        price_list.append(
            zoneKey=zone_key,
            datetime=_parse_label(period, end),
            currency="SGD",
            price=float(price),
            source=SOURCE,
        )
    return price_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print('fetch_price("SG") ->')
    print(fetch_price("SG"))
