from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any

from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER_NAME = "SEAPA.py"

SOURCE = "seapahydro.org"
DATA_URL = "https://seapahydro.org/api/scada/index"


def get_value(data: dict, key: str) -> float:
    return float(data[key]["text"])


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = session or Session()

    if target_datetime is not None:
        raise ParserException(
            PARSER_NAME, "This parser is not yet able to parse past dates", zone_key
        )

    res = session.get(DATA_URL)
    data = res.json()

    data = {
        "seapa_total": get_value(data, "ss_mw"),  # 2 hydro plants owned by SEAPA
        "ktn_hydro": get_value(
            data, "ktn_hydro_mw"
        ),  # hydro from pre-existing Ketchikan plants
        "ktn_diesel": get_value(data, "ktn_diesel_mw"),  # backup Ketchikan diesel
    }

    production_mix = ProductionMix(oil=data["ktn_diesel"])
    production_mix.add_value("hydro", data["seapa_total"], True)
    production_mix.add_value("hydro", data["ktn_hydro"], True)

    production_list = ProductionBreakdownList(logger=logger)
    production_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(timezone.utc),
        production=production_mix,
        source=SOURCE,
    )

    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print(fetch_production(ZoneKey("US-AK-SEAPA")))
