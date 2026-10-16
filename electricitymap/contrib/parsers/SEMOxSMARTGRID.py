"""Combined production parser for IE and GB-NIR.

SEM-O's metered data (see ``SEMO.py``) gives a full per-fuel breakdown but
reports lower wind and solar than EirGrid's SmartGridDashboard, which includes
distribution-connected generation. The two agree on the total. This parser
therefore takes **wind and solar from SmartGridDashboard** and **every other
mode (and storage) from SEMO**.

SEMO publishes on a 30-minute grid with a ~2-day lag, while SmartGridDashboard
is 15-minute and near-real-time. To align them, SmartGridDashboard's wind/solar
are fetched over a wider (weekly) window and averaged onto SEMO's 30-minute
timestamps, which define the output grid.

If only one source is available the parser returns that source's data on its own
and logs a warning; if neither is available it raises.
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


def _floor_to_half_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0 if dt.minute < 30 else 30, second=0, microsecond=0)


def _smartgrid_wind_solar(
    zone_key: ZoneKey, session: Session, target_datetime: datetime
) -> dict[datetime, dict[str, float]]:
    """Returns ``{utc_30min: {"wind": MW, "solar": MW}}`` from SmartGridDashboard.

    Uses the dashboard's weekly window (its public parser is limited to the
    current day) so the lagged SEMO timestamps are covered, and averages the
    15-minute values into 30-minute buckets to match SEMO's grid.
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
                "datefrom": (target_datetime - timedelta(days=5)).strftime("%Y-%m-%d"),
                "dateto": (target_datetime + timedelta(days=1)).strftime("%Y-%m-%d"),
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
            buckets[_floor_to_half_hour(dt)][mode].append(value)

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
    """Builds events on SEMO's grid: SmartGrid wind/solar + SEMO everything else."""
    breakdowns = ProductionBreakdownList(logger=logger)
    for event in semo_events:
        dt = event["datetime"]
        semo_production = event["production"]
        mix = ProductionMix()
        for mode, value in semo_production.items():
            if mode not in SMARTGRID_MODES and value is not None:
                mix.add_value(mode, value, correct_negative_with_zero=True)

        smartgrid = wind_solar.get(dt, {})
        for mode in SMARTGRID_MODES:
            # Prefer SmartGridDashboard; fall back to SEMO's own value if the
            # dashboard has no data for this timestamp.
            value = smartgrid.get(mode)
            if value is None:
                value = semo_production.get(mode)
            if value is not None:
                mix.add_value(mode, value, correct_negative_with_zero=True)

        storage = StorageMix(**event["storage"]) if event.get("storage") else None
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

    try:
        semo_events = SEMO.fetch_production(zone_key, session, target_datetime, logger)
    except Exception as error:
        logger.warning(f"SEMOxSMARTGRID: SEMO unavailable ({error})")
        semo_events = None

    try:
        wind_solar = _smartgrid_wind_solar(zone_key, session, target_datetime)
    except Exception as error:
        logger.warning(f"SEMOxSMARTGRID: SmartGridDashboard unavailable ({error})")
        wind_solar = None

    if not semo_events and not wind_solar:
        raise ParserException(
            parser="SEMOxSMARTGRID.py",
            message="Neither SEMO nor SmartGridDashboard returned data",
            zone_key=zone_key,
        )

    if not semo_events:
        logger.warning(
            "SEMOxSMARTGRID: only SmartGridDashboard is available; "
            "returning its production without the SEMO breakdown"
        )
        return SMARTGRIDDASHBOARD.fetch_production(
            zone_key, session, target_datetime, logger
        )

    if not wind_solar:
        logger.warning(
            "SEMOxSMARTGRID: only SEMO is available; returning its production "
            "with SEMO's own wind and solar"
        )
        return semo_events

    return _merge(zone_key, semo_events, wind_solar, logger)
