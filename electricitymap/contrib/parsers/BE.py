import json
import re
from datetime import datetime, timedelta, timezone
from itertools import groupby
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.parsers import ENTSOE
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

# API is limited to 100 items per query
# 2 hours * 4 (15 min intervals) * 12 (number of modes) = 96 items
TWO_HR_LIMIT = 2 * 4 * 12

ELIA_WINDOW_HOURS = (
    2  # Elia API max window per call (96 items = 2h * 4 intervals * 12 modes)
)

ELIA_API_ENDPOINT = "https://opendata.elia.be/api/explore/v2.1"
DATASET_ID_ELIA = "ods201"
BASE_URL_ELIA = f"{ELIA_API_ENDPOINT}/catalog/datasets/{DATASET_ID_ELIA}/records?order_by=datetime desc&limit={TWO_HR_LIMIT}"

SOURCE_ELIA = "opendata.elia.be"
TIMEZONE = ZoneInfo("Europe/Brussels")

FUEL_TYPE_MAPPING_ELIA = {
    "Fossil Gas": "gas",
    "Solar": "solar",
    "Waste": "biomass",
    "Wind Onshore": "wind",
    "Wind Offshore": "wind",
    "Biomass": "biomass",
    "Energy Storage": "storage_battery",
    "Nuclear": "nuclear",
    "Hydro Run-of-river and poundage": "hydro",
    "Hydro Pumped Storage": "storage_hydro",
    "Fossil Oil": "oil",
    "Other": "unknown",
}


_ELIA_RESOLUTION_PATTERN = re.compile(r"PT(\d+)([MH])")


def _elia_resolution_to_timedelta(resolution_code: str | None) -> timedelta | None:
    """Parses an Elia ISO-8601 resolution code (e.g. 'PT15M', 'PT1H')."""
    match = _ELIA_RESOLUTION_PATTERN.fullmatch(resolution_code or "")
    if match is None:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(minutes=value) if unit == "M" else timedelta(hours=value)


def fetch_elia(
    zone_key: ZoneKey = ZoneKey("BE"),
    session: Session | None = None,
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    session = session or Session()

    if start_datetime is not None and end_datetime is not None:
        start_brussels = start_datetime.astimezone(TIMEZONE).replace(tzinfo=None)
        end_brussels = end_datetime.astimezone(TIMEZONE).replace(tzinfo=None)
        url = f"{BASE_URL_ELIA}&timezone=Europe/Brussels&where=datetime >= date'{start_brussels.isoformat()}' AND datetime < date'{end_brussels.isoformat()}'"
    else:
        url = BASE_URL_ELIA

    response = session.get(url)
    results = json.loads(response.text).get("results", [])
    production_breakdown_list = ProductionBreakdownList(logger)

    sorted_results = sorted(results, key=lambda x: x.get("datetime", ""))

    for dt_key, events in groupby(sorted_results, key=lambda x: x.get("datetime")):
        events = list(events)
        production_mix = ProductionMix()

        for event in events:
            fuel_type = FUEL_TYPE_MAPPING_ELIA.get(
                event.get("fueltypeentsoe"), "unknown"
            )

            # Storage comes from ENTSO-E instead: ods201 only reports the
            # discharge side of pumped storage (never negative), while
            # ENTSO-E carries both generation and pumping.
            if "storage" in fuel_type:
                continue

            production_mix.add_value(
                fuel_type,
                event.get("generatedpower"),
            )

        dt = datetime.fromisoformat(dt_key).astimezone(timezone.utc)
        # Carry Elia's native resolution as the interval end so each 15-min
        # point spans exactly its own slot.
        resolution = _elia_resolution_to_timedelta(events[0].get("resolutioncode"))
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            end_datetime=dt + resolution if resolution else None,
            production=production_mix,
            source=SOURCE_ELIA,
        )

    return production_breakdown_list


ENTSOE_SPAN = (timedelta(hours=-48), timedelta(hours=0))


def fetch_entsoe(
    zone_key: ZoneKey = ZoneKey("BE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    session = session or Session()
    domain = ENTSOE.ENTSOE_DOMAIN_MAPPINGS[zone_key]
    params = {
        "documentType": "A75",
        "processType": "A16",
        "in_Domain": domain,
    }
    raw_production = ENTSOE.query_ENTSOE(
        session=session,
        params=params,
        span=ENTSOE_SPAN,
        target_datetime=target_datetime,
    )
    if raw_production is None:
        raise ParserException(
            parser="BE.py",
            message=f"No production data found for {zone_key} from ENTSOE",
            zone_key=zone_key,
        )
    return ENTSOE.parse_production(raw_production, logger, zone_key)


def _floor_to_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("BE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Combines Elia's 15-min production with ENTSO-E's hourly storage.

    Both feeds carry the same underlying data (Elia is the submitting TSO),
    but each signal has one best source: Elia has 15-min granularity for
    production, and ENTSO-E is the only feed with pumped-storage consumption
    (Elia ods201 only reports discharge). Each hourly ENTSO-E storage value is
    step-held onto the four 15-min slots of its hour: the hourly value is the
    average power over the hour, so repeating it preserves hourly energy and
    avoids fabricating a 15-min shape.
    """
    session = session or Session()

    entsoe_data = fetch_entsoe(zone_key, session, target_datetime, logger)

    # Fetch Elia over the same window as ENTSOE, in 2-hour chunks (API limit).
    reference_datetime = target_datetime or datetime.now(timezone.utc)
    range_end = reference_datetime + ENTSOE_SPAN[1]
    chunk_start = reference_datetime + ENTSOE_SPAN[0]
    elia_data = ProductionBreakdownList(logger)
    while chunk_start < range_end:
        chunk_end = chunk_start + timedelta(hours=ELIA_WINDOW_HOURS)
        chunk = fetch_elia(zone_key, session, chunk_start, chunk_end, logger)
        elia_data = ProductionBreakdownList.update_production_breakdowns(
            elia_data, chunk, logger
        )
        chunk_start = chunk_end

    entsoe_events_by_hour = {
        _floor_to_hour(event.datetime): event for event in entsoe_data.events
    }
    elia_hours = {_floor_to_hour(event.datetime) for event in elia_data.events}

    production_breakdowns = ProductionBreakdownList(logger)
    for event in elia_data.events:
        entsoe_event = entsoe_events_by_hour.get(_floor_to_hour(event.datetime))
        storage = (
            entsoe_event.storage.copy()
            if entsoe_event is not None and entsoe_event.storage is not None
            else None
        )
        production_breakdowns.append(
            zoneKey=event.zoneKey,
            datetime=event.datetime,
            end_datetime=event.end_datetime,
            production=event.production,
            storage=storage,
            source=f"{ENTSOE.SOURCE}, {SOURCE_ELIA}" if storage else SOURCE_ELIA,
        )

    # Hours where Elia has no data at all: fall back to the full ENTSOE event.
    for hour, entsoe_event in entsoe_events_by_hour.items():
        if hour not in elia_hours:
            production_breakdowns.append(
                zoneKey=entsoe_event.zoneKey,
                datetime=entsoe_event.datetime,
                end_datetime=entsoe_event.end_datetime,
                production=entsoe_event.production,
                storage=entsoe_event.storage,
                source=entsoe_event.source,
            )

    return production_breakdowns.to_list()


if __name__ == "__main__":
    fetch_elia(ZoneKey("BE"))
