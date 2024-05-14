from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER = "FO.py"
TIMEZONE = ZoneInfo("Atlantic/Faroe")

MAP_GENERATION = {
    "Vand": "hydro",
    "Olie": "oil",
    "Diesel": "oil",
    "Vind": "wind",
    "Sol": "solar",
    "Biogas": "biomass",
    "Tidal": "unknown",
}

VALID_ZONE_KEYS = ["FO", "FO-MI", "FO-SI"]


ZONE_KEY_TO_DATA_KEY = {
    "FO": "Sev_E",
    "FO-MI": "H_E",
    "FO-SI": "S_E",
}


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

    if target_datetime is not None:
        # There is a API endpoint at https://www.sev.fo/api/elproduction/last7days
        # but it's currently returning nothing at all. Last checked on 2022-08-09
        raise ParserException(
            PARSER, "This parser is not yet able to parse past dates", zone_key=zone_key
        )

    ses = session or Session()
    url = "https://www.sev.fo/api/realtimemap/now"
    response: Response = ses.get(url)
    obj = response.json()

    production_breakdown_list = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    for key, value in obj.items():
        if "Sum" in key or "Test" in key or "VnVand" in key:
            # "VnVand" is the sum of hydro (Mýrarnar + Fossá + Heygar)
            continue

        elif key.endswith(ZONE_KEY_TO_DATA_KEY[zone_key]):
            # E stands for Energy
            raw_generation_type: str = key.replace(ZONE_KEY_TO_DATA_KEY[zone_key], "")
            generation_type = MAP_GENERATION.get(raw_generation_type)
            if generation_type is None:
                raise ParserException(
                    PARSER, f"Unknown generation type: {raw_generation_type}", zone_key
                )
            # Power (MW)
            value = float(value.replace(",", "."))
            production_mix.add_value(generation_type, value)
        else:
            continue

    production_breakdown_list.append(
        zoneKey=zone_key,
        datetime=datetime.fromisoformat(obj["tiden"]).replace(tzinfo=TIMEZONE),
        source="sev.fo",
        production=production_mix,
    )
    return production_breakdown_list.to_list()


if __name__ == "__main__":
    for zone in VALID_ZONE_KEYS:
        print(fetch_production(zone_key=ZoneKey(zone)))
