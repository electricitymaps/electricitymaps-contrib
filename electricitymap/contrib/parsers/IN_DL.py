#!/usr/bin/env python3

from datetime import datetime, time
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.parsers.lib import IN, web, zonekey

ZONE_INFO = ZoneInfo

# Constant mapping of plant names to type
_PLANT_NAME_TO_TYPE = {
    "CCGT-Bawana": "gas",
    "DMSWSL-Dsidc": "biomass",
    "EDWPL-Gazipur": "biomass",
    "GT": "gas",
    "Pragati": "gas",
    "TOWMP-Okhla": "biomass",
    "TWEPL-TUGLAKABAD": "biomass",
}
_POWER_COLUMN_HEADER = "Actual"
_TOTAL_ROW_TITLE = "Total"


def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("IN-DL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetch Delhi consumption"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, "IN-DL")
    html = web.get_response_soup(
        zone_key, "http://www.delhisldc.org/Redirect.aspx", session
    )

    india_date_time = IN.read_datetime_from_span_id(
        html, "DynamicData1_LblDate", "%d-%b-%Y %I:%M:%S %p"
    )

    demand_value = IN.read_value_from_span_id(html, "DynamicData1_LblLoad")

    consumption_list = TotalConsumptionList(logger=logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=india_date_time,
        consumption=demand_value,
        source="delhisldc.org",
    )

    return consumption_list.to_list()


def fetch_production(
    zone_key: ZoneKey = ZoneKey("IN-DL"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetch Delhi production"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    production_mix = ProductionMix()
    default_types = ["gas", "biomass", "coal"]
    for plant_type in default_types:
        production_mix.add_value(plant_type, 0.0)

    zonekey.assert_zone_key(zone_key, "IN-DL")

    html = web.get_response_soup(
        zone_key, "http://www.delhisldc.org/Redirect.aspx?Loc=0804", session
    )

    india_time_string = IN.read_text_from_span_id(html, "ContentPlaceHolder3_ddgenco")
    india_time = time.fromisoformat(india_time_string)
    india_date_time = datetime.combine(datetime.now(IN.ZONE_INFO), india_time).replace(
        tzinfo=IN.ZONE_INFO
    )

    prod_table = html.find("table", {"id": "ContentPlaceHolder3_dgenco"})
    prod_rows = prod_table.findAll("tr")

    # Determine the index of the column that contains the actual power values
    header_row = prod_rows[0]
    column_headers = [cell.text for cell in header_row.findAll("td")]
    try:
        value_column_index = column_headers.index(_POWER_COLUMN_HEADER)
    except ValueError as e:
        raise ValueError(
            f"Could not find a column with header '{_POWER_COLUMN_HEADER}' in the scraped HTML table"
        ) from e

    for row in prod_rows[1:]:
        cells = row.findAll("td")
        plant_name = cells[0].text
        if plant_name == _TOTAL_ROW_TITLE:
            continue
        try:
            plant_type = _PLANT_NAME_TO_TYPE[plant_name]
        except KeyError as e:
            raise KeyError(
                f"Unknown plant '{plant_name}'; manually add the type of this plant to `_PLANT_NAME_TO_TYPE`"
            ) from e
        power = max(0.0, float(cells[value_column_index].text))
        production_mix.add_value(plant_type, power)

    production_breakdowns = ProductionBreakdownList(logger)
    production_breakdowns.append(
        zoneKey=zone_key,
        datetime=india_date_time,
        production=production_mix,
        source="delhisldc.org",
    )

    return production_breakdowns.to_list()


if __name__ == "__main__":
    session = Session()
    print(fetch_production("IN-DL", session))
    print(fetch_consumption("IN-DL", session))
