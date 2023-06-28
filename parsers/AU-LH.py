from datetime import datetime, timezone
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional, Union
import time

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
    TotalProductionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

from requests_html import HTMLSession


PARSER_NAME = "AU-LH.py"
DATA_URL = "http://photonscada.com/data/perspective/client/LHI"

RENDER_TIMEOUT = 10 # seconds

def validate_and_clean_data(
    zone_key: ZoneKey,
    values: List[str]
) -> List[float]:
    if len(values) != 8:
        raise ParserException(PARSER_NAME, "Unexpected number of values parsed", zone_key)
    
    even_index_values = values[::2]
    if not all(val == "L" for val in even_index_values):
        raise ParserException(PARSER_NAME, "Unexpected parsed values (although normally discarded), website structure changed", zone_key)

    odd_index_values = values[1::2]
    cleaned_values = []

    for val in odd_index_values:
        # Observed units are always kW, this could be a wrong assumption
        unit_suffix = " kW"
        if not val.endswith(unit_suffix):
            raise ParserException(PARSER_NAME, f"Unexpected parsed values, check website structure or electricity units {odd_index_values}", zone_key)
        
        # strip suffix, convert to numerical value, convert units to MW
        parsed_val = float(val.rstrip(unit_suffix))/1000
        num_digits = 10
        cleaned_values.append(round(parsed_val, num_digits))

    return cleaned_values


def fetch_data(
    zone_key: ZoneKey,
    session: HTMLSession
) -> Dict[str, float]:
    res = session.get(DATA_URL)

    if not res.status_code == 200:
        raise ParserException(
            PARSER_NAME,
            f"Exception when fetching production error code: {res.status_code}",
            zone_key,
        )
    
    # render the website using request_html (chromium), need a sleep value to wait for render
    res.html.render(timeout=RENDER_TIMEOUT + 1, sleep=RENDER_TIMEOUT)

    # values in the DOM are poorly structured
    # thankfully the values we want are returned in tspans
    tspan_list = res.html.find("tspan")
    parsed_values = [tspan.text for tspan in tspan_list]

    cleaned_values = validate_and_clean_data(zone_key, parsed_values)

    return {
        "consumption": cleaned_values[0],
        "solar": cleaned_values[1],
        "battery": cleaned_values[2],
        "diesel": cleaned_values[3]
    }
    

def fetch_production(
    zone_key: ZoneKey,
    session: HTMLSession = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    if target_datetime is not None:
        raise ParserException(PARSER_NAME, "This parser is not yet able to parse past dates", zone_key)
    
    is_new_session = session is None
    if is_new_session:
        session = HTMLSession()

    data = fetch_data(zone_key, session)

    production_list = ProductionBreakdownList(logger=logger)
    production_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(timezone.utc),
        production=ProductionMix(
            gas=data["diesel"],
            solar=data["solar"],
        ),
        # storage=StorageMix(hydro=item["hydroStorage"] * -1),
        source=DATA_URL,
    )

    if is_new_session:
        session.close()

    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print(fetch_production(ZoneKey("AU-LH")))
