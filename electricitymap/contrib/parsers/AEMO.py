import csv
import io
import json
import re
import zipfile
from collections.abc import Iterable, Iterator
from datetime import date, datetime, timedelta, timezone
from logging import Logger, getLogger
from typing import Any, NamedTuple
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import EventSourceType
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.parsers.lib.session import mount_retry
from electricitymap.contrib.types import ZoneKey

SOURCE = "aemo.com.au"

ZONE_KEY_TO_REGION = {
    "AU-NSW": "NSW1",
    "AU-QLD": "QLD1",
    "AU-SA": "SA1",
    "AU-TAS": "TAS1",
    "AU-VIC": "VIC1",
    "AU-WA": "WEM",  # a market of its own, read from the WEM feeds below
}

ZONE_KEY_TO_TIMEZONE = {
    "AU-NSW": ZoneInfo("Australia/Sydney"),
    "AU-QLD": ZoneInfo("Australia/Brisbane"),
    "AU-SA": ZoneInfo("Australia/Adelaide"),
    "AU-TAS": ZoneInfo("Australia/Hobart"),
    "AU-VIC": ZoneInfo("Australia/Melbourne"),
    "AU-WA": ZoneInfo("Australia/Perth"),
}

# --- Dispatch and forecast reports ------------------------------------------
#
# AEMO publishes the metered flow of every interconnector and the operational
# demand of every region, so a border is read directly instead of being
# reconstructed from region aggregates the way OPENNEM.fetch_exchange has to.
# The OPENNEM parsers are kept so the two can be compared.

REFETCH_FREQUENCY = timedelta(days=7)
DISPATCH_INTERVAL = timedelta(minutes=5)
# AEMO stamps every dispatch row with SETTLEMENTDATE, the END of the interval:
# dispatch interval 241 of the trading day starting 04:00 covers 00:00-00:05 and
# is stamped 00:05. Events are therefore emitted at SETTLEMENTDATE minus one
# interval. OPENNEM passes the same stamp through untouched, so its events read
# one interval later than these for the same physical interval.
MARKET_TIMEZONE = ZoneInfo("Australia/Brisbane")  # AEST year round, never DST
CSV_DATETIME_FORMAT = "%Y/%m/%d %H:%M:%S"

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
    "PUBLIC_ARCHIVE%23{report}{table}%23FILE01%23{year}{month:02d}010000.zip",
    "PUBLIC_DVD_{report}{table}_{year}{month:02d}010000.zip",
)
# Every live interval is a separate ~20 kB file, so a live call reads one hour.
LIVE_INTERVALS = 12

FORECAST_DEMAND_URL = (
    "https://nemweb.com.au/Reports/Current/Operational_Demand/FORECAST_HH/"
)


class ReportTable(NamedTuple):
    """A table of an AEMO report, as tagged inside its CSVs."""

    report: str
    table: str


INTERCONNECTOR_RES = ReportTable("DISPATCH", "INTERCONNECTORRES")
REGION_SUM = ReportTable("DISPATCH", "REGIONSUM")
FORECAST_DEMAND = ReportTable("OPERATIONAL_DEMAND", "FORECAST")

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
    if region != "WEM"
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


def _rows_from_csv(lines: Iterable[str], rows: ReportTable) -> Iterator[dict[str, str]]:
    """
    Rows of one table of an AEMO report.

    AEMO reports interleave tables in one CSV: an `I` row names the columns of
    the `D` rows that follow it, both tagged with the report and table they
    belong to.
    """
    columns: list[str] | None = None
    for row in csv.reader(lines):
        if len(row) < 4 or (row[1], row[2]) != rows:
            continue
        if row[0] == "I":
            columns = row[4:]
        elif row[0] == "D" and columns is not None:
            # not strict: the column set differs between AEMO's schema versions,
            # and each file names its own, so pair what this file declares
            yield dict(zip(columns, row[4:], strict=False))


def _rows_from_zip(blob: bytes, rows: ReportTable) -> Iterator[dict[str, str]]:
    """Rows of one table of a report archive, which may nest further zips."""
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".zip"):
                # daily archives hold one zip per dispatch interval, and zipfile
                # needs those seekable, so they are the one case read in full
                yield from _rows_from_zip(archive.read(name), rows)
                continue
            # a monthly archive holds ~50 MB of CSV, so stream it
            with archive.open(name) as member:
                yield from _rows_from_csv(
                    io.TextIOWrapper(member, encoding="utf-8", errors="replace"), rows
                )


def _get_if_published(session: Session, url: str) -> bytes | None:
    """Body of an archive, or None when AEMO has not published it."""
    response = session.get(url)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.content


def _fetch_monthly_archive(
    session: Session, year: int, month: int, rows: ReportTable
) -> bytes | None:
    """A month of one table's rows, under whichever name AEMO filed it."""
    for filename in MONTHLY_DISPATCH_FILENAMES:
        blob = _get_if_published(
            session,
            MMSDM_DATA_URL.format(year=year, month=month)
            + filename.format(year=year, month=month, **rows._asdict()),
        )
        if blob is not None:
            return blob
    return None


def _listed_reports(session: Session, base_url: str, pattern: str) -> list[str]:
    """Names of the reports a directory lists, oldest first."""
    listing = session.get(base_url)
    listing.raise_for_status()
    names = sorted(set(re.findall(pattern, listing.text)))
    if not names:
        raise ParserException(
            parser="AEMO", message=f"No reports matching {pattern} listed at {base_url}"
        )
    return names


def _fetch_report_rows(
    session: Session, base_url: str, name: str, rows: ReportTable
) -> Iterator[dict[str, str]]:
    """Rows of one published report."""
    response = session.get(base_url + name)
    response.raise_for_status()
    yield from _rows_from_zip(response.content, rows)


def _fetch_live_rows(session: Session, rows: ReportTable) -> Iterator[dict[str, str]]:
    """Rows of the most recent dispatch intervals."""
    names = _listed_reports(
        session, CURRENT_DISPATCH_URL, r"PUBLIC_DISPATCHIS_\d{12}_\d+\.zip"
    )
    for name in names[-LIVE_INTERVALS:]:
        yield from _fetch_report_rows(session, CURRENT_DISPATCH_URL, name, rows)


def _fetch_forecast_rows(
    session: Session, target_datetime: datetime
) -> Iterator[dict[str, str]]:
    """Rows of the last half-hourly demand forecast published on a date."""
    names = _listed_reports(
        session,
        FORECAST_DEMAND_URL,
        rf"PUBLIC_FORECAST_OPERATIONAL_DEMAND_HH_{target_datetime:%Y%m%d}\d+_\d+\.zip",
    )
    yield from _fetch_report_rows(
        session, FORECAST_DEMAND_URL, names[-1], FORECAST_DEMAND
    )


def _fetch_archived_rows(
    session: Session,
    rows: ReportTable,
    window: tuple[datetime, datetime],
    logger: Logger,
) -> Iterator[dict[str, str]]:
    """
    Rows covering a window, taken from the monthly archive where it is published,
    the daily archive for the days it does not cover, and the live reports for
    the current day.
    """
    start, end = window
    days = set()
    day = start.date()
    while day <= end.date():
        days.add(day)
        day += timedelta(days=1)

    for year, month in sorted({(d.year, d.month) for d in days}):
        blob = _fetch_monthly_archive(session, year, month, rows)
        if blob is None:
            continue
        days -= {d for d in days if (d.year, d.month) == (year, month)}
        yield from _rows_from_zip(blob, rows)

    today = datetime.now(tz=MARKET_TIMEZONE).date()
    for day in sorted(days):
        if day >= today:
            yield from _fetch_live_rows(session, rows)
            continue
        blob = _get_if_published(
            session, f"{ARCHIVE_DISPATCH_URL}PUBLIC_DISPATCHIS_{day:%Y%m%d}.zip"
        )
        if blob is None:
            logger.warning(f"AEMO has no published dispatch data for {day}")
            continue
        yield from _rows_from_zip(blob, rows)


def _dispatch_intervals(
    session: Session,
    table: ReportTable,
    target_datetime: datetime | None,
    zone_key: ZoneKey,
    logger: Logger,
) -> Iterator[tuple[dict[str, str], datetime, datetime]]:
    """
    Rows of one dispatch table, paired with the interval each covers.

    Reads the live reports when no target datetime is given and the archives
    covering the refetch window otherwise, keeping the rows inside that window
    and those of the normal dispatch run - an intervention interval is published
    twice, with the same metered values in both. Raises when the window has no
    published rows.
    """
    if target_datetime is None:
        rows = _fetch_live_rows(session, table)
        window = None
    else:
        end = target_datetime.astimezone(MARKET_TIMEZONE)
        window = (end - REFETCH_FREQUENCY, end)
        rows = _fetch_archived_rows(session, table, window, logger)

    published = False
    for row in rows:
        published = True
        if row["INTERVENTION"] != "0":
            continue
        settlement = datetime.strptime(
            row["SETTLEMENTDATE"], CSV_DATETIME_FORMAT
        ).replace(tzinfo=MARKET_TIMEZONE)
        if window and not window[0] < settlement <= window[1]:
            continue
        yield row, settlement - DISPATCH_INTERVAL, settlement

    if window and not published:
        raise ParserException(
            parser="AEMO",
            message=f"AEMO published no {table.table} data for {window[0]:%Y-%m-%d} to {window[1]:%Y-%m-%d}. "
            "Per-table monthly archives start in 2015; earlier months are only "
            "distributed as whole-month bundles of every table.",
            zone_key=zone_key,
        )


# --- WEM operational demand -------------------------------------------------
#
# AU-WA is the Wholesale Electricity Market, a market of its own on a host of
# its own publishing JSON and CSV rather than the NEM's report archives, so it
# does not share the dispatch plumbing above. Three feeds cover it:
#   - the real-time estimate, a single instantaneous reading;
#   - one file per day of settled 5 minute dispatch intervals, published about
#     two days late, which is what the refetch reads;
#   - the balancing summary of the years before WEMDE, half hourly.

WEM_TIMEZONE = ZoneInfo("Australia/Perth")  # AWST, +08:00 year round, never DST
WEM_DISPATCH_INTERVAL = timedelta(minutes=5)
WEM_TRADING_INTERVAL = timedelta(minutes=30)  # the pre-WEMDE resolution
# A missing day older than this is missing rather than merely unpublished.
WEM_PUBLICATION_LAG = timedelta(days=3)

WEM_REALTIME_URL = (
    "https://data.wa.aemo.com.au/public/market-data/wemde/operationalDemandWithdrawal/"
    "realTime/OperationalDemandAndWithdrawalEstimate.json"
)
WEM_DAILY_URL = (
    "https://data.wa.aemo.com.au/public/market-data/wemde/operationalDemandWithdrawal/"
    "dailyFiles/OperationalDemandAndWithdrawal_{day}.json"
)
WEM_BALANCING_SUMMARY_URL = (
    "https://data.wa.aemo.com.au/public/public-data/datafiles/balancing-summary/"
    "balancing-summary-{year}.csv"
)
# WEMDE dispatched its first interval on 2023-10-01 and ran in parallel from
# this instant, which is where the balancing summary before it hands over.
WEM_DISPATCH_START = datetime(2023, 9, 26, tzinfo=timezone.utc)
BALANCING_SUMMARY_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DemandInterval(NamedTuple):
    """Demand in MW over one interval."""

    start: datetime
    end: datetime
    demand: float


def _utc_days(start: datetime, end: datetime) -> list[date]:
    """The UTC days a half-open window touches, oldest first."""
    days = []
    day = start.astimezone(timezone.utc).date()
    # end is exclusive, so a window ending at midnight stops the day before
    last = (end - timedelta(minutes=1)).astimezone(timezone.utc).date()
    while day <= last:
        days.append(day)
        day += timedelta(days=1)
    return days


def _wem_live_interval(session: Session) -> Iterator[DemandInterval]:
    """
    The dispatch interval in progress, from AEMO's real-time estimate.

    The estimate is one instantaneous reading rather than a series, so a live
    call yields a single interval, stamped at the start of the interval the
    reading falls in - where the refetch later files the settled value over it.
    """
    response = session.get(WEM_REALTIME_URL)
    response.raise_for_status()
    row = response.json()["data"]["data"]
    demand = row.get("operationalDemandEstimate")
    if demand is None:
        return
    as_at = datetime.fromisoformat(row["asAtTimeStamp"])
    minutes = int(WEM_DISPATCH_INTERVAL.total_seconds() // 60)
    start = as_at.replace(second=0, microsecond=0) - timedelta(
        minutes=as_at.minute % minutes
    )
    yield DemandInterval(start, start + WEM_DISPATCH_INTERVAL, float(demand))


def _wem_dispatch_intervals(session: Session, day: date) -> Iterator[DemandInterval]:
    """Settled dispatch intervals of one UTC day, empty when unpublished."""
    blob = _get_if_published(session, WEM_DAILY_URL.format(day=day.isoformat()))
    if blob is None:
        return
    for row in json.loads(blob)["data"]["data"]:
        if row["operationalDemand"] is None:
            continue
        yield DemandInterval(
            # dispatchInterval is the start of the interval and asAtTimeStamp
            # its end, the opposite of the NEM's single SETTLEMENTDATE stamp
            datetime.fromisoformat(row["dispatchInterval"]),
            datetime.fromisoformat(row["asAtTimeStamp"]),
            float(row["operationalDemand"]),
        )


def _wem_trading_intervals(session: Session, year: int) -> Iterator[DemandInterval]:
    """
    Half-hourly intervals of one pre-WEMDE year, empty when unpublished.

    Operational demand is not published for these years, so this is total sent
    out generation, which over the five days the two feeds overlap tracks it to
    a -5 MW mean bias and 28 MW mean absolute on a 2 GW system.
    """
    blob = _get_if_published(session, WEM_BALANCING_SUMMARY_URL.format(year=year))
    if blob is None:
        return
    for row in csv.DictReader(io.StringIO(blob.decode("utf-8", errors="replace"))):
        # a row short of columns reads as unfilled rather than as a value
        generation = row["Total Generation (MW)"]
        if not generation:
            continue
        start = datetime.strptime(
            row["Trading Interval"], BALANCING_SUMMARY_DATETIME_FORMAT
        ).replace(tzinfo=WEM_TIMEZONE)
        yield DemandInterval(start, start + WEM_TRADING_INTERVAL, float(generation))


def _wem_demand_intervals(
    session: Session,
    target_datetime: datetime | None,
    zone_key: ZoneKey,
    logger: Logger,
) -> Iterator[DemandInterval]:
    """
    Operational demand of the WEM, live or over the refetch window.

    Both archives file a day, and a year, by its UTC bounds - the file named
    2026-08-24 holds the intervals from 08:00 AWST that day to 07:55 the next -
    so the window is walked in UTC days. Each feed is read only over the range
    it covers, so the days the two overlap are not reported at both
    resolutions. Raises when neither feed published anything for those days.
    """
    if target_datetime is None:
        yield from _wem_live_interval(session)
        return

    end = target_datetime.astimezone(timezone.utc)
    window = (end - REFETCH_FREQUENCY, end)
    summary_days = _utc_days(window[0], min(window[1], WEM_DISPATCH_START))
    dispatch_days = _utc_days(max(window[0], WEM_DISPATCH_START), window[1])
    published_by = datetime.now(tz=timezone.utc).date() - WEM_PUBLICATION_LAG

    published = 0
    for year in sorted({day.year for day in summary_days}):
        intervals = list(_wem_trading_intervals(session, year))
        if not intervals:
            logger.warning(f"AEMO has no published WEM balancing summary for {year}")
        published += len(intervals)
        yield from (
            interval
            for interval in intervals
            if window[0] <= interval.start < min(window[1], WEM_DISPATCH_START)
        )

    for day in dispatch_days:
        intervals = list(_wem_dispatch_intervals(session, day))
        # the daily files run about two days behind, so a missing recent day is
        # expected - the refetch reaching it next reads it
        if not intervals and day < published_by:
            logger.warning(f"AEMO has no published WEM demand for {day}")
        published += len(intervals)
        yield from (
            interval
            for interval in intervals
            if window[0] <= interval.start < window[1]
        )

    if not published:
        raise ParserException(
            parser="AEMO",
            message=f"AEMO published no WEM demand for {window[0]:%Y-%m-%d} to {window[1]:%Y-%m-%d}. "
            f"Dispatch intervals start {WEM_DISPATCH_START:%Y-%m-%d} and the "
            "balancing summary before them starts 2012-07-01.",
            zone_key=zone_key,
        )


def _nem_demand_intervals(
    session: Session,
    region: str,
    target_datetime: datetime | None,
    zone_key: ZoneKey,
    logger: Logger,
) -> Iterator[DemandInterval]:
    """Operational demand of one NEM region, as dispatched (`TOTALDEMAND`)."""
    for row, start, end in _dispatch_intervals(
        session, REGION_SUM, target_datetime, zone_key, logger
    ):
        if row["REGIONID"] != region or not row["TOTALDEMAND"]:
            continue
        yield DemandInterval(start, end, float(row["TOTALDEMAND"]))


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
    session = mount_retry(session or Session())
    exchange_key = ZoneKey("->".join(sorted([zone_key1, zone_key2])))
    interconnectors = EXCHANGE_KEY_TO_INTERCONNECTORS.get(exchange_key)
    if interconnectors is None:
        raise ParserException(
            parser="AEMO",
            message=f"Valid exchange keys for this parser are {sorted(EXCHANGE_KEY_TO_INTERCONNECTORS)}, you passed {exchange_key=}",
            zone_key=exchange_key,
        )

    # AEMO republishes an interval under a new sequence number when it is
    # revised, and the archives overlap around midnight, so the same flow can
    # arrive twice. ExchangeList collapses those onto the last one appended,
    # which is the newest revision since the sources are read oldest first.
    contributions = {
        interconnector: ExchangeList(logger) for interconnector in interconnectors
    }
    unmapped: set[str] = set()
    for row, start, end in _dispatch_intervals(
        session, INTERCONNECTOR_RES, target_datetime, exchange_key, logger
    ):
        interconnector = row["INTERCONNECTORID"]
        if interconnector not in INTERCONNECTOR_TO_REGIONS:
            unmapped.add(interconnector)
            continue
        if interconnector not in interconnectors or not row["METEREDMWFLOW"]:
            continue
        contributions[interconnector].append(
            zoneKey=exchange_key,
            datetime=start,
            end_datetime=end,
            netFlow=interconnectors[interconnector] * float(row["METEREDMWFLOW"]),
            source=SOURCE,
        )

    if unmapped:
        # Not an error for the borders we do know, but a new interconnector means
        # a new border, which needs an exchange of its own in config/exchanges.
        logger.warning(
            f"AEMO dispatched interconnectors this parser does not map: {sorted(unmapped)}"
        )

    # The lines of a border are parts of one flow, so an interval one of them is
    # missing from is dropped rather than summed short.
    return ExchangeList.merge_exchanges(
        list(contributions.values()), logger, drop_non_matching_datetimes=True
    ).to_list()


@refetch_frequency(REFETCH_FREQUENCY)
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Operational demand of an Australian market region.

    The NEM regions are read from dispatch (`TOTALDEMAND`), AU-WA from the WEM
    feeds, which are a different host and format on their own resolutions.
    """
    session = mount_retry(session or Session())
    region = ZONE_KEY_TO_REGION.get(zone_key)
    if region is None:
        raise ParserException(
            parser="AEMO",
            message=f"Valid zone keys for this parser are {sorted(ZONE_KEY_TO_REGION)}, you passed {zone_key=}",
            zone_key=zone_key,
        )

    intervals = (
        _wem_demand_intervals(session, target_datetime, zone_key, logger)
        if region == "WEM"
        else _nem_demand_intervals(session, region, target_datetime, zone_key, logger)
    )
    # A republished interval arrives twice; TotalConsumptionList keeps the last.
    consumption = TotalConsumptionList(logger)
    for start, end, demand in intervals:
        consumption.append(
            zoneKey=zone_key,
            datetime=start,
            end_datetime=end,
            consumption=demand,
            source=SOURCE,
        )
    return consumption.to_list()


def fetch_consumption_forecast(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Consumption forecast in MW every half an hour for 10 days ahead.

    Only the NEM regions are covered by this report; the WEM load forecast is
    published elsewhere, so AU-WA returns an empty list.
    """
    session = mount_retry(session or Session())
    region = ZONE_KEY_TO_REGION.get(zone_key)
    if region not in REGION_TO_ZONE_KEY:
        return []  # only the NEM regions are forecast
    if target_datetime is None:
        target_datetime = datetime.now(tz=ZONE_KEY_TO_TIMEZONE[zone_key])

    consumption = TotalConsumptionList(logger)
    for row in _fetch_forecast_rows(session, target_datetime):
        if row["REGIONID"] != region:
            continue
        consumption.append(
            zoneKey=zone_key,
            datetime=datetime.strptime(
                row["INTERVAL_DATETIME"], CSV_DATETIME_FORMAT
            ).replace(tzinfo=ZONE_KEY_TO_TIMEZONE[zone_key]),
            # 50% probability of exceedance operational demand forecast value
            consumption=float(row["OPERATIONAL_DEMAND_POE50"]),
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )
    return consumption.to_list()


if __name__ == "__main__":
    """Main method, never used by the electricityMap backend, but handy for testing."""

    print(fetch_consumption_forecast("AU-NSW"))
    print(fetch_consumption_forecast("AU-QLD"))
    print(fetch_consumption_forecast("AU-SA"))
    print(fetch_consumption_forecast("AU-TAS"))
    print(fetch_consumption_forecast("AU-VIC"))
    print(fetch_consumption_forecast("AU-WA"))  # not forecast, an empty list

    print(fetch_consumption("AU-WA"))
    print(
        fetch_consumption("AU-WA", target_datetime=datetime.fromisoformat("2015-06-15"))
    )

    print(fetch_exchange("AU-NSW", "AU-QLD"))
    print(
        fetch_exchange(
            "AU-TAS", "AU-VIC", target_datetime=datetime.fromisoformat("2015-06-15")
        )
    )
