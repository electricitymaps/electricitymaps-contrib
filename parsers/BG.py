from datetime import datetime, timezone
from logging import Logger, getLogger

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER = "BG.py"

SOURCE = "eso.bg"
SOURCE_API_URL = "http://www.eso.bg/api/rabota_na_EEC_json.php?en"

PRODUCTION_TYPE_TO_PRODUCTION_MODE = {
    "NPP": "nuclear",
    "CHP": "coal",
    "Heating TPPs": "gas",
    "Factory TPPs": "gas",
    "HPP": "hydro",
    "Small HPPs": "hydro",
    "Wind": "wind",
    "PV": "solar",
    "Bio": "biomass",
}


def fetch_production(
    zone_key: ZoneKey = ZoneKey("BG"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    session = session or Session()

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    time = datetime.now(timezone.utc)
    response = session.get(SOURCE_API_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    response_payload = response.json()
    logger.debug(f"Raw generation breakdown: {response_payload}")

    production_mix = ProductionMix()
    for header, value in response_payload:
        production_type, _delimiter, _percentage = header.rpartition(" ")
        production_mode = PRODUCTION_TYPE_TO_PRODUCTION_MODE[production_type]
        production_mix.add_value(production_mode, value)

    production_breakdown_list = ProductionBreakdownList(logger)
    production_breakdown_list.append(
        zoneKey=zone_key,
        datetime=time,
        source=SOURCE,
        production=production_mix,
    )
    return production_breakdown_list.to_list()
