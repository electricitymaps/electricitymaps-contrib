from datetime import datetime, time, timedelta, timezone
from itertools import groupby
from logging import Logger, getLogger
from operator import itemgetter
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

PARSER = "FO.py"
TIMEZONE = ZoneInfo("Atlantic/Faroe")

MAP_PRODUCTION_MODE = {
    "Water": "hydro",
    "Oil": "oil",
    "Wind": "wind",
    "Solar": "solar",
    "Biogas": "biomass",
}

MAP_PRODUCTION_MODE_REALTIME_API = {
    "Vand": "hydro",
    "Olie": "oil",
    "Diesel": "oil",
    "Vind": "wind",
    "Sol": "solar",
    "Biogas": "biomass",
    "Tidal": "unknown",
}

MAP_ZONE_KEY_TO_REALTIME_API_DATA_KEY = {
    "FO": "Sev_E",
    "FO-MI": "H_E",
    "FO-SI": "S_E",
}

VALID_ZONE_KEYS = [ZoneKey("FO"), ZoneKey("FO-MI"), ZoneKey("FO-SI")]


def _fetch_production_historical(
    zone_key: ZoneKey,
    session: Session,
    target_datetime_utc: datetime,
    logger: Logger,
) -> ProductionBreakdownList:
    """Fetches production breakdown data from the historical API for the target zone and date of interest.

    Data has hourly granularity and spans 48 h (the target day and the previous one).

    Note that when requesting data for the current day not all data will be available: data for the hour seems to
    be getting published at hour + 2:25 h, so data for the last 2 or 3 hours will not be available.

    Also note that earliest retrievable target date is 2022/01/01, which might not enough historical data to enable
    TSA estimations. It is therefore recommended to supplement this API with a realtime API for the time being.

    References:
        https://www.sev.fo/framleidsla/hagtoel
    """

    # API provides max one day of backlog
    target_date_utc_to = datetime.combine(
        target_datetime_utc, time(), tzinfo=timezone.utc
    )
    target_date_utc_from = target_date_utc_to - timedelta(days=1)

    # API takes local days as query parameters and returns data for the corresponding interval as UTC
    target_date_local_to = target_date_utc_to.astimezone(tz=TIMEZONE)
    target_date_local_from = target_date_utc_from.astimezone(tz=TIMEZONE)

    # during SDT local time is UTC + 0 so day boundaries align
    # but during DST local time is UTC + 1 so the data for UTC 23:00 is at 00:00 of the next local day, which will thus need to be requested
    if target_date_local_to.dst():
        target_date_local_to = target_date_local_to + timedelta(days=1)

    url = f"https://www.sev.fo/api/elproduction/search?type=item&group=powerplant&from={target_date_local_from.strftime('%Y%m%d')}170000&to={target_date_local_to.strftime('%Y%m%d')}170000"
    response = session.get(url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    hourly_production_for_each_power_plant = response.json()

    production_breakdown_list = ProductionBreakdownList(logger)

    hourly_production_for_each_power_plant_by_hour = groupby(
        hourly_production_for_each_power_plant, key=itemgetter("date")
    )
    for hour, group in hourly_production_for_each_power_plant_by_hour:
        dt = datetime.fromisoformat(hour).replace(tzinfo=timezone.utc)

        # filter out entries outside of time window of interest (which happens if DST)
        end_of_day = target_date_utc_to + timedelta(days=1) - timedelta(microseconds=1)
        if dt < target_date_utc_from or dt > end_of_day:
            continue

        production_mix = ProductionMix()

        for power_plant_data in group:
            # filter out entries for areas that are not relevant
            area = power_plant_data["area"]
            if (
                zone_key == ZoneKey("FO-MI")
                and area != "Main"
                or zone_key == ZoneKey("FO-SI")
                and area != "South"
            ):
                continue

            production_mode = MAP_PRODUCTION_MODE[power_plant_data["motivepower"]]
            production_mix.add_value(production_mode, power_plant_data["mwh"])

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source="sev.fo",
            production=production_mix,
        )

    return production_breakdown_list


def _fetch_production_live(
    zone_key: ZoneKey,
    session: Session,
    logger: Logger,
) -> ProductionBreakdownList:
    """Fetches 'instantaneous' production breakdown data from the live API for the target zone and date of interest.

    Data seems to be getting updated roughly every 2 mn.

    References:
        https://www.sev.fo/framleidsla/el-orka-i-foroyum
    """
    url = "https://www.sev.fo/api/realtimemap/now"
    response = session.get(url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    obj = response.json()

    production_breakdown_list = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    for key, value in obj.items():
        if "Sum" in key or "Test" in key or "VnVand" in key:
            # "VnVand" is the sum of hydro (Mýrarnar + Fossá + Heygar)
            continue

        data_key = MAP_ZONE_KEY_TO_REALTIME_API_DATA_KEY[zone_key]
        if key.endswith(data_key):
            # E stands for Energy
            raw_generation_type: str = key.replace(data_key, "")
            generation_type = MAP_PRODUCTION_MODE_REALTIME_API.get(raw_generation_type)
            if generation_type is None:
                raise ParserException(
                    PARSER,
                    f"Unknown generation type: {raw_generation_type}",
                    zone_key,
                )
            # Power (MW)
            value = float(value.replace(",", "."))
            production_mix.add_value(generation_type, value)
        else:
            continue

    dt = (
        datetime.fromisoformat(obj["tiden"])
        # floor to hourly granularity to match historical API entries
        .replace(minute=0, second=0, microsecond=0, tzinfo=TIMEZONE)
        # cast to UTC just to keep consistent with historical API entries
        .astimezone(timezone.utc)
    )

    production_breakdown_list.append(
        zoneKey=zone_key,
        datetime=dt,
        source="sev.fo",
        production=production_mix,
    )

    return production_breakdown_list


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("FO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    if zone_key not in VALID_ZONE_KEYS:
        raise ParserException(
            PARSER,
            f"This parser cannot retrieve data for zone {zone_key!r}",
        )

    now = datetime.now(timezone.utc)
    target_datetime = (
        now if target_datetime is None else target_datetime.astimezone(timezone.utc)
    )

    session = session or Session()

    historical_production_breakdown_list = _fetch_production_historical(
        zone_key=zone_key,
        session=session,
        target_datetime_utc=target_datetime,
        logger=logger,
    )

    # historical API has a ~2:25h delay, so supplement with realtime API data if applicable
    # note that this will still leave a small gap, but at least it will provide a realtime signal
    if target_datetime > historical_production_breakdown_list.events[-1].datetime:
        live_production_breakdown_list = _fetch_production_live(
            zone_key=zone_key,
            session=session,
            logger=logger,
        )
    else:
        live_production_breakdown_list = ProductionBreakdownList(logger)

    # favour historical data on merge as realtime data is not representative of hourly production and / or might be stale
    return ProductionBreakdownList.update_production_breakdowns(
        live_production_breakdown_list,
        historical_production_breakdown_list,
        logger=logger,
    ).to_list()


if __name__ == "__main__":
    for zone_key in VALID_ZONE_KEYS:
        print(fetch_production(zone_key))
        print(fetch_production(zone_key, target_datetime=datetime(2023, 7, 16, 12)))
