from datetime import datetime, time, timedelta, timezone
from itertools import groupby
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

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

VALID_ZONE_KEYS = ["FO", "FO-MI", "FO-SI"]


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

    # API provides max one day of backlog
    target_date_utc_to = datetime.combine(target_datetime, time(), tzinfo=timezone.utc)
    target_date_utc_from = target_date_utc_to - timedelta(days=1)

    # API takes local days as query parameters and returns data for the corresponding interval as UTC
    target_date_local_to = target_date_utc_to.astimezone(tz=TIMEZONE)
    target_date_local_from = target_date_utc_from.astimezone(tz=TIMEZONE)

    # during SDT local time is UTC + 0 so day boundaries align
    # but during DST local time is UTC + 1 so the data for UTC 23:00 is at 00:00 of the next local day, which will thus need to be requested
    if target_date_local_to.dst():
        target_date_local_to = target_date_local_to + timedelta(days=1)

    url = f"https://www.sev.fo/api/elproduction/search?type=item&group=powerplant&from={target_date_local_from.strftime('%Y%m%d')}170000&to={target_date_local_to.strftime('%Y%m%d')}170000"
    ses = session or Session()
    response: Response = ses.get(url)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    hourly_production_for_each_power_plant = response.json()

    production_breakdown_list = ProductionBreakdownList(logger)

    hourly_production_for_each_power_plant_by_hour = groupby(
        hourly_production_for_each_power_plant, key=lambda x: x["date"]
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

    # historical API has a ~2:25h delay, so supplement with realtime API data if applicable
    # note that this will still leave a gap, but at least it will provide a realtime signal
    if target_datetime > production_breakdown_list.events[-1].datetime:
        url = "https://www.sev.fo/api/realtimemap/now"
        response: Response = ses.get(url)
        if not response.ok:
            raise ParserException(
                PARSER,
                f"Exception when fetching production error code: {response.status_code}: {response.text}",
                zone_key,
            )

        obj = response.json()

        live_production_mix = ProductionMix()
        for key, value in obj.items():
            if "Sum" in key or "Test" in key or "VnVand" in key:
                # "VnVand" is the sum of hydro (Mýrarnar + Fossá + Heygar)
                continue

            data_key = MAP_ZONE_KEY_TO_REALTIME_API_DATA_KEY[zone_key]
            if key.endswith(data_key):
                # E stands for Energy
                raw_generation_type: str = key.replace(data_key, "")
                generation_type = MAP_PRODUCTION_MODE_REALTIME_API.get(
                    raw_generation_type
                )
                if generation_type is None:
                    raise ParserException(
                        PARSER,
                        f"Unknown generation type: {raw_generation_type}",
                        zone_key,
                    )
                # Power (MW)
                value = float(value.replace(",", "."))
                live_production_mix.add_value(generation_type, value)
            else:
                continue

        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(obj["tiden"])
            .replace(tzinfo=TIMEZONE)
            .astimezone(timezone.utc),  # to keep consistent with historical API entries
            source="sev.fo",
            production=live_production_mix,
        )

    return production_breakdown_list.to_list()


if __name__ == "__main__":
    for zone in VALID_ZONE_KEYS:
        print(fetch_production(zone_key=ZoneKey(zone)))
        print(
            fetch_production(
                zone_key=ZoneKey(zone), target_datetime=datetime(2023, 7, 16, 12)
            )
        )
