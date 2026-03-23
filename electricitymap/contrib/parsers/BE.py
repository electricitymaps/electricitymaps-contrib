import json
from datetime import datetime, timedelta
from itertools import groupby
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
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


def fetch_elia(
    zone_key: ZoneKey = ZoneKey("BE"),
    session: Session | None = None,
    start_datetime: datetime | None = None,
    end_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> ProductionBreakdownList:
    session = session or Session()

    if start_datetime is not None and end_datetime is not None:
        url = f"{BASE_URL_ELIA}&timezone=Europe/Brussels&where=datetime >= date'{start_datetime.replace(tzinfo=None).isoformat()}' AND datetime < date'{end_datetime.replace(tzinfo=None).isoformat()}'"
    else:
        url = BASE_URL_ELIA

    response = session.get(url)
    results = json.loads(response.text).get("results", [])
    production_breakdown_list = ProductionBreakdownList(logger)

    sorted_results = sorted(results, key=lambda x: x.get("datetime", ""))

    for dt_key, events in groupby(sorted_results, key=lambda x: x.get("datetime")):
        production_mix = ProductionMix()
        storage_mix = StorageMix()

        for event in events:
            fuel_type = FUEL_TYPE_MAPPING_ELIA.get(
                event.get("fueltypeentsoe"), "unknown"
            )
            power = event.get("generatedpower")

            if "storage" in fuel_type:
                storage_mix.add_value(
                    fuel_type.removeprefix("storage_"),
                    power,
                )
            else:
                production_mix.add_value(
                    fuel_type,
                    power,
                )

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(dt_key),
            production=production_mix,
            storage=storage_mix,
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


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("BE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()

    entsoe_data = fetch_entsoe(zone_key, session, target_datetime, logger)
    # Determine the time range covered by ENTSOE data and fetch Elia in 2-hour chunks.
    entsoe_datetimes = [event.datetime for event in entsoe_data.events]
    elia_data = ProductionBreakdownList(logger)

    if entsoe_datetimes:
        range_start = min(entsoe_datetimes)
        range_end = max(entsoe_datetimes)
        chunk_start = range_start
        while chunk_start <= range_end:
            chunk_end = chunk_start + timedelta(hours=ELIA_WINDOW_HOURS)
            chunk = fetch_elia(zone_key, session, chunk_start, chunk_end, logger)
            elia_data = ProductionBreakdownList.update_production_breakdowns(
                elia_data, chunk, logger
            )
            chunk_start = chunk_end

    # Prefer Elia data where available; fall back to ENTSOE for other datetimes.
    return ProductionBreakdownList.update_production_breakdowns(
        entsoe_data, elia_data, logger
    ).to_list()


if __name__ == "__main__":
    fetch_elia(ZoneKey("BE"))
