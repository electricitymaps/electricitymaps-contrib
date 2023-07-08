from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional, Union

from requests import Response, Session
from requests_html import HTMLSession

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER_NAME = "US_AK_SAP.py"

SOURCE = "seapahydro.org"
DATA_URL = "https://seapahydro.org/scada"


def get_value_by_id(res: Response, id) -> float:
    return float(res.html.find(f"#{id}", first=True).text)


def fetch_production(
    zone_key: ZoneKey,
    session: Session = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    if target_datetime is not None:
        raise ParserException(
            PARSER_NAME, "This parser is not yet able to parse past dates", zone_key
        )

    session = HTMLSession()
    res = session.get(DATA_URL)
    # render the website using requests_html (chromium) due to JS scripts
    res.html.render()

    data = {
        "seapa_total": get_value_by_id(res, "ss_mw"),  # 2 hydro plants owned by SEAPA
        "ktn_hydro": get_value_by_id(
            res, "ktn_hydro_mw"
        ),  # hydro from pre-existing Ketchikan plants
        "ktn_diesel": get_value_by_id(res, "ktn_diesel_mw"),  # backup Ketchikan diesel
    }

    production_list = ProductionBreakdownList(logger=logger)
    production_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(timezone.utc),
        production=ProductionMix(
            gas=data["ktn_diesel"],
            hydro=data["seapa_total"] + data["ktn_hydro"],
        ),
        source=SOURCE,
    )

    session.close()

    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print(fetch_production(ZoneKey("AU-LH")))
