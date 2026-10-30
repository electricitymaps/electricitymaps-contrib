"""Combined production parser for IE and GB-NIR.

SEM-O's metered data (see ``SEMO.py``) gives a full per-fuel breakdown but
reports lower wind and solar than EirGrid's SmartGridDashboard, which includes
distribution-connected generation. The two agree on the total. This parser
therefore takes **wind and solar from SmartGridDashboard** and **every other
mode (and storage) from SEMO**.

SEMO publishes on a 30-minute grid with a ~2-day lag, while SmartGridDashboard
is 15-minute and near-real-time. SmartGridDashboard's wind/solar are fetched
over a wider (weekly) window and averaged onto 30-minute timestamps. The output
covers the union of both grids: where SEMO has caught up the event carries the
full breakdown, and the most recent timestamps (SEMO not yet published) carry
SmartGridDashboard wind/solar only.

Wind and solar always come from SmartGridDashboard and are never taken from
SEMO. SEMO defines the breakdown and is required: BM-086 only retains ~3 months,
so for an older target SEMO returns nothing and the parser returns no data
(rather than SmartGridDashboard wind/solar on their own) to avoid a refetch
overwriting a previously stored full breakdown. If SmartGridDashboard is
unavailable the output carries SEMO's breakdown without wind/solar; a SEMO
failure is raised.
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers import SEMO, SMARTGRIDDASHBOARD
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

SOURCE = "sem-o.com, eirgridgroup.com"
# Modes sourced from SmartGridDashboard; everything else comes from SEMO.
SMARTGRID_MODES = ("wind", "solar")


def _half_hour_label(dt: datetime) -> datetime:
    """Labels a 15-minute reading with the half-hour that ends its window.

    SmartGridDashboard readings fall on :00, :15, :30 and :45, and each
    30-minute value is labelled at the end of its window (so it averages the
    previous and current reading). That maps:

        :15 and :30 -> :30            (e.g. 06:30 uses 06:15 and 06:30)
        :45         -> the next :00
        :00         -> itself (already a window end)
    """
    dt = dt.replace(second=0, microsecond=0)
    if dt.minute == 0:
        return dt
    if dt.minute <= 30:
        return dt.replace(minute=30)
    return dt.replace(minute=0) + timedelta(hours=1)


def _smartgrid_wind_solar(
    zone_key: ZoneKey, session: Session, target_datetime: datetime
) -> dict[datetime, dict[str, float]]:
    """Returns ``{utc_30min: {"wind": MW, "solar": MW}}`` from SmartGridDashboard.

    The dashboard API serves historical data when given the ``dateRange`` +
    camel-case ``dateFrom``/``dateTo`` (``dd-MMM-yyyy``) parameters; the
    lower-case ``datefrom``/``dateto`` used elsewhere are silently ignored and
    only ever return the current day. A weekly window starting two days before
    the target covers the days around ``target_datetime``. The 15-minute
    readings are averaged into the 30-minute value ending each window.
    """
    region = SMARTGRIDDASHBOARD.REGION_MAPPING[zone_key]

    def fetch(kind: str) -> dict[datetime, float]:
        response = session.get(
            SMARTGRIDDASHBOARD.URL,
            params={
                "areas": SMARTGRIDDASHBOARD.KINDS_AREA_MAPPING[kind],
                "chartType": "default",
                "region": region,
                "dateRange": "week",
                "dateFrom": (target_datetime - timedelta(days=2)).strftime("%d-%b-%Y"),
                "dateTo": (target_datetime + timedelta(days=1)).strftime("%d-%b-%Y"),
            },
        )
        response.raise_for_status()
        values: dict[datetime, float] = {}
        for row in response.json().get("Rows", []):
            if row.get("EffectiveTime") and row.get("Value") is not None:
                dt = SMARTGRIDDASHBOARD.parse_datetime(row["EffectiveTime"]).astimezone(
                    timezone.utc
                )
                values[dt] = row["Value"]
        return values

    series = {mode: fetch(mode) for mode in SMARTGRID_MODES}

    buckets: dict[datetime, dict[str, list[float]]] = defaultdict(
        lambda: {mode: [] for mode in SMARTGRID_MODES}
    )
    for mode, values in series.items():
        for dt, value in values.items():
            buckets[_half_hour_label(dt)][mode].append(value)

    return {
        dt: {
            mode: (sum(vals) / len(vals) if vals else None)
            for mode, vals in modes.items()
        }
        for dt, modes in buckets.items()
    }


def _merge(
    zone_key: ZoneKey,
    semo_events: list[dict],
    wind_solar: dict[datetime, dict[str, float]],
    logger: Logger,
) -> list:
    """Builds events over the union of both grids: SmartGrid wind/solar plus
    SEMO everything else.

    Timestamps newer than SEMO's latest (the publication lag) still appear,
    carrying SmartGridDashboard wind/solar only. SmartGrid-only timestamps that
    are not newer than SEMO's data are dropped so the parser never emits a
    wind/solar-only event for a period SEMO should (or did) cover.
    """
    semo_by_datetime = {event["datetime"]: event for event in semo_events}
    latest_semo = max(semo_by_datetime) if semo_by_datetime else None
    breakdowns = ProductionBreakdownList(logger=logger)

    for dt in sorted(set(semo_by_datetime) | set(wind_solar)):
        event = semo_by_datetime.get(dt)
        if event is None and (latest_semo is None or dt <= latest_semo):
            continue

        mix = ProductionMix()
        storage = None

        if event is not None:
            for mode, value in event["production"].items():
                if mode not in SMARTGRID_MODES and value is not None:
                    mix.add_value(mode, value, correct_negative_with_zero=True)
            storage = StorageMix(**event["storage"]) if event.get("storage") else None

        # Wind/solar come only from SmartGridDashboard; a missing value is left
        # unset rather than falling back to SEMO's (lower) metered value.
        smartgrid = wind_solar.get(dt, {})
        for mode in SMARTGRID_MODES:
            value = smartgrid.get(mode)
            if value is not None:
                mix.add_value(mode, value, correct_negative_with_zero=True)

        breakdowns.append(
            zoneKey=zone_key,
            production=mix,
            storage=storage,
            datetime=dt,
            source=SOURCE,
        )
    return breakdowns.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Wind/solar from SmartGridDashboard, all other modes from SEMO."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=timezone.utc)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)

    # SmartGridDashboard ignores the requested dates and always returns data up
    # to now, so restrict the output to the days around target_datetime (the
    # same window SEMO queries) instead of stretching it up to the present.
    window_start = (target_datetime - timedelta(days=2)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    window_end = (target_datetime + timedelta(days=1)).replace(
        hour=23, minute=59, second=59, microsecond=0
    )

    # SEMO defines the breakdown. A SEMO failure is surfaced rather than falling
    # back to a wind/solar-only result that would overwrite a stored full
    # breakdown on refetch.
    try:
        semo_events = SEMO.fetch_production(zone_key, session, target_datetime, logger)
    except Exception as error:
        raise ParserException(
            parser="SEMOxSMARTGRID.py",
            message=f"SEMO unavailable: {error}",
            zone_key=zone_key,
        ) from error

    # BM-086 only retains ~3 months, so older refetches return nothing. Stop here
    # instead of emitting SmartGridDashboard wind/solar on their own, which would
    # overwrite the previously stored SEMO + SmartGridDashboard breakdown.
    if not semo_events:
        logger.warning(
            f"SEMOxSMARTGRID: no SEM-O data around "
            f"{target_datetime:%Y-%m-%d %H:%M} (beyond SEM-O's ~3-month BM-086 "
            "retention); returning no data to avoid overwriting stored values"
        )
        return []

    try:
        wind_solar = _smartgrid_wind_solar(zone_key, session, target_datetime)
        wind_solar = {
            dt: value
            for dt, value in wind_solar.items()
            if window_start <= dt <= window_end
        }
    except Exception as error:
        logger.warning(
            f"SEMOxSMARTGRID: SmartGridDashboard unavailable ({error}); "
            "returning the SEMO breakdown without wind and solar"
        )
        wind_solar = {}

    return _merge(zone_key, semo_events, wind_solar, logger)
