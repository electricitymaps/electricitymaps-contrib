import csv
import io
import re
import zipfile
from collections import Counter
from collections.abc import Iterable, Iterator
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

SOURCE = "aemo.com.au"

ZONE_KEY_TO_REGION = {
    "AU-NSW": "NSW1",
    "AU-QLD": "QLD1",
    "AU-SA": "SA1",
    "AU-TAS": "TAS1",
    "AU-VIC": "VIC1",
    "AU-WA": "WEM",  # This zone is not implemented yet
}

ZONE_KEY_TO_TIMEZONE = {
    "AU-NSW": ZoneInfo("Australia/Sydney"),
    "AU-QLD": ZoneInfo("Australia/Brisbane"),
    "AU-SA": ZoneInfo("Australia/Adelaide"),
    "AU-TAS": ZoneInfo("Australia/Hobart"),
    "AU-VIC": ZoneInfo("Australia/Melbourne"),
    "AU-WA": ZoneInfo("Australia/Perth"),  # This zone is not implemented yet
}

# TODO, what about the other zone in Australia (AU-WA)? Check remaining zone


def find_document(session, target_datetime):
    # Fetch the directory listing
    base_url = "http://nemweb.com.au/Reports/CURRENT/Operational_Demand/FORECAST_HH/"
    response = session.get(base_url)

    # Parse with BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # String datetime
    target_date_str = target_datetime.strftime("%Y%m%d")

    # Find matching links
    matching_links = soup.find_all(
        "a",
        href=re.compile(
            rf"PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_{target_date_str}\d+_\d+\.zip"
        ),
    )

    if matching_links:
        target_link = matching_links[-1]  # Get the last (most recent) link
        full_url = urljoin(base_url, target_link["href"])  # Construct full URL

        file_response = session.get(full_url)

        with zipfile.ZipFile(io.BytesIO(file_response.content)) as z:
            csv_filename = z.namelist()[0]
            with z.open(csv_filename) as f:
                df = pd.read_csv(f)
                return df
    else:
        print("No matching files found")


def fetch_consumption_forecast(
    zone_key: ZoneKey,  # "AU-NSW", "AU-QLD", "AU-SA", "AU-TAS", "AU-VIC", "AU-WA"
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Consumption forecast in MW every half an hour for 10 days ahead.
    Only for NSW1, QND1, SA1, TAS1, VIC1 zones."""
    session = session or Session()

    if target_datetime is None:
        target_datetime = datetime.now(tz=ZONE_KEY_TO_TIMEZONE[zone_key])

    df = find_document(session, target_datetime)

    # Transform dataframe
    df.columns = df.iloc[0]
    df = df.iloc[1:-1].reset_index(drop=True)

    #
    region = ZONE_KEY_TO_REGION.get(zone_key)
    all_consumption_events = df[
        df["REGIONID"] == region
    ]  # all events with a datetime and a consumption value
    consumption_list = TotalConsumptionList(logger)
    for _, event in all_consumption_events.iterrows():
        datetime_object = datetime.strptime(
            event["INTERVAL_DATETIME"], "%Y/%m/%d %H:%M:%S"
        ).replace(tzinfo=ZONE_KEY_TO_TIMEZONE[zone_key])

        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime_object,
            consumption=float(
                event["OPERATIONAL_DEMAND_POE50"]
            ),  # 50% probability of exceedance operational demand forecast value
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


# --- Exchanges --------------------------------------------------------------
#
# AEMO publishes the metered flow of every interconnector, so a border is read
# directly instead of being reconstructed from region aggregates the way
# OPENNEM.fetch_exchange has to. Both parsers are kept so they can be compared.

REFETCH_FREQUENCY = timedelta(days=7)
DISPATCH_INTERVAL = timedelta(minutes=5)
# AEMO stamps every dispatch row with SETTLEMENTDATE, the END of the interval:
# dispatch interval 241 of the trading day starting 04:00 covers 00:00-00:05 and
# is stamped 00:05. Events are therefore emitted at SETTLEMENTDATE minus one
# interval. OPENNEM passes the same stamp through untouched, so its events read
# one interval later than these for the same physical interval.
MARKET_TIMEZONE = ZoneInfo("Australia/Brisbane")  # AEST year round, never DST
SETTLEMENT_FORMAT = "%Y/%m/%d %H:%M:%S"

CURRENT_DISPATCH_URL = "https://nemweb.com.au/Reports/Current/DispatchIS_Reports/"
ARCHIVE_DISPATCH_URL = "https://nemweb.com.au/Reports/Archive/DispatchIS_Reports/"
MMSDM_DATA_URL = (
    "https://nemweb.com.au/Data_Archive/Wholesale_Electricity/MMSDM/{year}/"
    "MMSDM_{year}_{month:02d}/MMSDM_Historical_Data_SQLLoader/DATA/"
)
# AEMO renamed the monthly archives partway through the series - older months are
# PUBLIC_DVD_..., newer ones PUBLIC_ARCHIVE#...#FILE01#... - so try both rather
# than pin the changeover, which sits somewhere before 2025-10.
MONTHLY_DISPATCH_FILENAMES = (
    "PUBLIC_ARCHIVE%23DISPATCHINTERCONNECTORRES%23FILE01%23{year}{month:02d}010000.zip",
    "PUBLIC_DVD_DISPATCHINTERCONNECTORRES_{year}{month:02d}010000.zip",
)
# Every live interval is a separate ~20 kB file, so a live call reads one hour.
LIVE_INTERVALS = 12

# The region pair each interconnector runs between, from AEMO's INTERCONNECTOR
# table (REGIONFROM, REGIONTO). Flows are positive from REGIONFROM to REGIONTO.
INTERCONNECTOR_TO_REGIONS = {
    "NSW1-QLD1": ("NSW1", "QLD1"),  # QNI
    "N-Q-MNSP1": ("NSW1", "QLD1"),  # Directlink / Terranora
    "VIC1-NSW1": ("VIC1", "NSW1"),  # VNI
    "V-SA": ("VIC1", "SA1"),  # Heywood
    "V-S-MNSP1": ("VIC1", "SA1"),  # Murraylink
    "T-V-MNSP1": ("TAS1", "VIC1"),  # Basslink
}

REGION_TO_ZONE_KEY = {
    region: zone_key
    for zone_key, region in ZONE_KEY_TO_REGION.items()
    if region != "WEM"  # WEM is a separate grid with no interconnectors
}


def _exchange_key_and_direction(
    region_from: str, region_to: str
) -> tuple[ZoneKey, int]:
    """Exchange key for a region pair, and the sign AEMO's flow enters it with."""
    zone_from = REGION_TO_ZONE_KEY[region_from]
    zone_to = REGION_TO_ZONE_KEY[region_to]
    exchange_key = ZoneKey("->".join(sorted([zone_from, zone_to])))
    # netFlow is positive when the zone on the left of the arrow is exporting
    return exchange_key, 1 if sorted([zone_from, zone_to])[0] == zone_from else -1


EXCHANGE_KEY_TO_INTERCONNECTORS: dict[ZoneKey, dict[str, int]] = {}
for _interconnector, _regions in INTERCONNECTOR_TO_REGIONS.items():
    _key, _direction = _exchange_key_and_direction(*_regions)
    EXCHANGE_KEY_TO_INTERCONNECTORS.setdefault(_key, {})[_interconnector] = _direction


def _rows_from_csv(lines: Iterable[str]) -> Iterator[dict[str, str]]:
    """
    Interconnector rows of an AEMO report.

    AEMO reports interleave tables in one CSV: an `I` row names the columns of
    the `D` rows that follow it, both tagged with the table they belong to.
    """
    columns: list[str] | None = None
    for row in csv.reader(lines):
        if len(row) < 4 or row[1] != "DISPATCH" or row[2] != "INTERCONNECTORRES":
            continue
        if row[0] == "I":
            columns = row[4:]
        elif row[0] == "D" and columns is not None:
            # not strict: the column set differs between AEMO's schema versions,
            # and each file names its own, so pair what this file declares
            yield dict(zip(columns, row[4:], strict=False))


def _rows_from_zip(blob: bytes) -> Iterator[dict[str, str]]:
    """Interconnector rows of a report archive, which may nest further zips."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for name in archive.namelist():
            member = archive.read(name)
            if name.lower().endswith(".zip"):
                # daily archives hold one zip per dispatch interval
                yield from _rows_from_zip(member)
            else:
                yield from _rows_from_csv(
                    io.StringIO(member.decode("utf-8", errors="replace"))
                )


def _get_if_published(session: Session, url: str) -> bytes | None:
    """Body of an archive, or None when AEMO has not published it."""
    response = session.get(url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.content


def _fetch_monthly_archive(session: Session, year: int, month: int) -> bytes | None:
    """A month of interconnector rows, under whichever name AEMO filed it."""
    for filename in MONTHLY_DISPATCH_FILENAMES:
        blob = _get_if_published(
            session,
            MMSDM_DATA_URL.format(year=year, month=month)
            + filename.format(year=year, month=month),
        )
        if blob is not None:
            return blob
    return None


def _fetch_live_rows(session: Session) -> Iterator[dict[str, str]]:
    """Rows of the most recent dispatch intervals."""
    listing = session.get(CURRENT_DISPATCH_URL)
    listing.raise_for_status()
    names = sorted(set(re.findall(r"PUBLIC_DISPATCHIS_\d{12}_\d+\.zip", listing.text)))
    if not names:
        raise ParserException(
            parser="AEMO",
            message=f"No dispatch reports listed at {CURRENT_DISPATCH_URL}",
        )
    for name in names[-LIVE_INTERVALS:]:
        response = session.get(CURRENT_DISPATCH_URL + name)
        response.raise_for_status()
        yield from _rows_from_zip(response.content)


def _fetch_archived_rows(
    session: Session, start: datetime, end: datetime, logger: Logger
) -> Iterator[dict[str, str]]:
    """
    Rows covering a window, taken from the monthly archive where it is published,
    the daily archive for the days it does not cover, and the live reports for
    the current day.
    """
    days = set()
    day = start.date()
    while day <= end.date():
        days.add(day)
        day += timedelta(days=1)

    for year, month in sorted({(d.year, d.month) for d in days}):
        blob = _fetch_monthly_archive(session, year, month)
        if blob is None:
            continue
        days -= {d for d in days if (d.year, d.month) == (year, month)}
        yield from _rows_from_zip(blob)

    today = datetime.now(tz=MARKET_TIMEZONE).date()
    for day in sorted(days):
        if day >= today:
            yield from _fetch_live_rows(session)
            continue
        blob = _get_if_published(
            session, f"{ARCHIVE_DISPATCH_URL}PUBLIC_DISPATCHIS_{day:%Y%m%d}.zip"
        )
        if blob is None:
            logger.warning(f"AEMO has no published dispatch data for {day}")
            continue
        yield from _rows_from_zip(blob)


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Net flow across a NEM border, summed over the interconnectors that form it.

    Datetimes not reported by every interconnector of the border are dropped, and
    interconnectors this parser does not map are logged.
    """
    session = session or Session()
    exchange_key = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    interconnectors = EXCHANGE_KEY_TO_INTERCONNECTORS.get(exchange_key)
    if interconnectors is None:
        raise ParserException(
            parser="AEMO",
            message=f"Valid exchange keys for this parser are {sorted(EXCHANGE_KEY_TO_INTERCONNECTORS)}, you passed {exchange_key=}",
            zone_key=exchange_key,
        )

    if target_datetime is None:
        rows = _fetch_live_rows(session)
        window: tuple[datetime, datetime] | None = None
    else:
        end = target_datetime.astimezone(MARKET_TIMEZONE)
        window = (end - REFETCH_FREQUENCY, end)
        rows = _fetch_archived_rows(session, *window, logger)

    contributions = {
        interconnector: ExchangeList(logger) for interconnector in interconnectors
    }
    # AEMO republishes an interval under a new sequence number when it is
    # revised, and the archives overlap around midnight, so the same flow can
    # arrive twice. Merging sums whatever it is given, so drop repeats here.
    seen: set[tuple[str, datetime]] = set()
    unmapped: set[str] = set()
    published = False
    for row in rows:
        published = True
        interconnector = row["INTERCONNECTORID"]
        if interconnector not in INTERCONNECTOR_TO_REGIONS:
            unmapped.add(interconnector)
            continue
        if interconnector not in interconnectors:
            continue
        # An intervention interval is published twice, as the physical run and
        # the pricing run. Metered flow is the same in both, so keep one.
        if row["INTERVENTION"] != "0" or not row["METEREDMWFLOW"]:
            continue
        settlement = datetime.strptime(
            row["SETTLEMENTDATE"], SETTLEMENT_FORMAT
        ).replace(tzinfo=MARKET_TIMEZONE)
        if window and not window[0] < settlement <= window[1]:
            continue
        if (interconnector, settlement) in seen:
            continue
        seen.add((interconnector, settlement))
        contributions[interconnector].append(
            zoneKey=exchange_key,
            datetime=settlement - DISPATCH_INTERVAL,
            end_datetime=settlement,
            netFlow=interconnectors[interconnector] * float(row["METEREDMWFLOW"]),
            source=SOURCE,
        )

    if window and not published:
        raise ParserException(
            parser="AEMO",
            message=f"AEMO published no dispatch data for {window[0]:%Y-%m-%d} to {window[1]:%Y-%m-%d}. "
            "Per-table monthly archives start in 2015; earlier months are only "
            "distributed as whole-month bundles of every table.",
            zone_key=exchange_key,
        )

    if unmapped:
        # Not an error for the borders we do know, but a new interconnector means
        # a new border, which needs an exchange of its own in config/exchanges.
        logger.warning(
            f"AEMO dispatched interconnectors this parser does not map: {sorted(unmapped)}"
        )

    merged = ExchangeList.merge_exchanges(
        list(contributions.values()), logger
    ).to_list()

    # Merging sums the lines it is given, so an interval one line did not report
    # would come out understated rather than missing. Drop those.
    reported = Counter(settlement for _, settlement in seen)
    events = [
        event
        for event in merged
        if reported[event["end_datetime"]] == len(interconnectors)
    ]
    if len(events) < len(merged):
        logger.warning(
            f"Skipping {len(merged) - len(events)} interval(s) of {exchange_key} where "
            f"not all of {sorted(interconnectors)} reported a flow"
        )
    return events


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print(fetch_consumption_forecast("AU-NSW"))
    print(fetch_consumption_forecast("AU-QLD"))
    print(fetch_consumption_forecast("AU-SA"))
    print(fetch_consumption_forecast("AU-TAS"))
    print(fetch_consumption_forecast("AU-VIC"))
    print(
        fetch_consumption_forecast("AU-WA")
    )  # Not implemented yet. It returns an empty list

    print(fetch_exchange("AU-NSW", "AU-QLD"))
    print(
        fetch_exchange(
            "AU-TAS", "AU-VIC", target_datetime=datetime.fromisoformat("2015-06-15")
        )
    )
