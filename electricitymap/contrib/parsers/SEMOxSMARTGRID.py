"""Combined production parser for IE and GB-NIR.

SEM-O's metered data (see ``SEMO.py``) gives a full per-fuel breakdown but
reports lower wind and solar than EirGrid's SmartGridDashboard, which includes
distribution-connected generation. The two agree on the total. This parser
therefore takes **wind and solar from SmartGridDashboard** and **every other
mode (and storage) from SEMO**.

SEMO publishes on a 30-minute grid with a lag of ~1.5 days on weekdays and more
over weekends (no publication on Saturday and Sunday). SmartGridDashboard is
15-minute and near-real-time; its wind/solar are averaged onto 30-minute
timestamps. **Only timestamps SEMO covers are emitted**, so every event is a
full breakdown. The most recent timestamps (SEMO not yet published) are left
empty and filled downstream by the estimation pipeline, which uses the wind and
solar forecasts; the daily refetch completes them once SEM-O publishes.

Wind and solar always come from SmartGridDashboard and are never taken from
SEMO. If SmartGridDashboard is unavailable the output carries SEMO's breakdown
without wind/solar; a SEMO failure is raised.
"""

from collections import defaultdict
from datetime import UTC, datetime, timedelta
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.parsers import SEMO, SMARTGRIDDASHBOARD
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

SOURCE = "eirgridgroup.com,sem-o.com"
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
    zone_key: ZoneKey,
    session: Session,
    start_datetime: datetime,
    end_datetime: datetime,
) -> dict[datetime, dict[str, float]]:
    """Returns ``{utc_30min: {"wind": MW, "solar": MW}}`` from SmartGridDashboard
    for the ``[start_datetime, end_datetime]`` window.

    The dashboard API serves historical data when given the ``dateRange`` +
    camel-case ``dateFrom``/``dateTo`` (``dd-MMM-yyyy``) parameters; the
    lower-case ``datefrom``/``dateto`` used elsewhere are silently ignored and
    only ever return the current day. The 15-minute readings are averaged into
    the 30-minute value ending each window.
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
                "dateFrom": start_datetime.strftime("%d-%b-%Y"),
                "dateTo": end_datetime.strftime("%d-%b-%Y"),
            },
        )
        response.raise_for_status()
        values: dict[datetime, float] = {}
        for row in response.json().get("Rows", []):
            if row.get("EffectiveTime") and row.get("Value") is not None:
                dt = SMARTGRIDDASHBOARD.parse_datetime(row["EffectiveTime"]).astimezone(
                    UTC
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
    """Builds one event per SEMO timestamp: SEMO's breakdown with wind and solar
    from SmartGridDashboard. SmartGrid timestamps SEMO does not cover are
    dropped, so the parser never emits a partial (wind/solar-only) breakdown."""
    breakdowns = ProductionBreakdownList(logger=logger)

    for event in sorted(semo_events, key=lambda e: e["datetime"]):
        dt = event["datetime"]
        mix = ProductionMix()
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
        target_datetime = datetime.now(tz=UTC)
    elif target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=UTC)

    # This window is the single source of truth: it is passed to both SEMO and
    # SmartGridDashboard so the two sources always cover the same range. It
    # reaches two days back to cover SEMO's publication lag; the upper bound
    # keeps SmartGridDashboard (which can return data up to now) from stretching
    # the output to the present.
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
        semo_events = SEMO.fetch_production_range(
            zone_key, session, window_start, window_end, logger
        )
    except Exception as error:
        raise ParserException(
            parser="SEMOxSMARTGRID.py",
            message=f"SEMO unavailable: {error}",
            zone_key=zone_key,
        ) from error

    # Nothing to emit without SEMO: SEM-O has not published the window yet (live,
    # over weekends) or it is beyond BM-086's ~3-month retention (refetch).
    if not semo_events:
        logger.warning(
            f"SEMOxSMARTGRID: no SEM-O data around {target_datetime:%Y-%m-%d %H:%M}"
            " (not published yet, or beyond BM-086's ~3-month retention)"
        )
        return []

    try:
        wind_solar = _smartgrid_wind_solar(zone_key, session, window_start, window_end)
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
