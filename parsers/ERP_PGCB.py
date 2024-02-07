#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Tag
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    TotalConsumptionList,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

# Power Grid Company of Bangladesh: erp.pgcb.gov.bd
# Has table (also historical) of production, consumption and exchange.
# This table gets updated batch-wise every few hours, so most of the time, the delay will be >2h.

TIMEZONE = ZoneInfo("Asia/Dhaka")
LATEST_URL = "https://erp.pgcb.gov.bd/web/generations/view_generations"
HISTORICAL_URL = (
    "https://erp.pgcb.gov.bd/web/generations/view_generations?search="  # DD-MM-YYYY
)
SOURCE = "erp.pgcb.gov.bd"
TABLE_HEADERS = [
    "Date",
    "Time",
    "Generation(MW)",
    "Demand(MW)",
    "Loadshed",
    "Gas",
    "Liquid Fuel",
    "Coal",
    "Hydro",
    "Solar",
    "Wind",
    "Bheramara HVDC",
    "Tripura",
    "Remarks",
]


def table_entry_to_float(entry: str):
    """
    Helper function to handle empty cells in table.
    """
    if entry == "":
        return None
    try:
        return float(entry)
    except ValueError as e:
        raise ParserException(
            parser="BD.py",
            message=(f'Failed to parse entry: "{entry}" to float in table.'),
        ) from e


def parse_table_body(table_body: Tag) -> list[dict]:
    """
    Parse the table body returned by the URL.
    Returns a list of rows represented by dicts.
    """

    rows = table_body.find_all("tr")
    row_data = []

    for row in rows:
        row_items = row.find_all("td")
        row_items = [item.text.strip() for item in row_items]

        # date and time in [0]; [1] are DD-MM-YYYY; HH:mm[:ss]
        parsed_day = datetime.strptime(row_items[0], "%d-%m-%Y").date()
        try:
            assert isinstance(row_items[1], str)
            if row_items[1][0:2] == "24":
                # The endpoint is reporting 24:00:00 as 00:00:00 of the next day, so we need to fix that.
                row_items[1] = row_items[1].replace("24", "00", 1)
                parsed_day += timedelta(days=1)
            # newer data points are in HH:mm:ss format
            parsed_time = datetime.strptime(row_items[1], "%H:%M:%S").time()
        except ValueError:
            # very old data points are sometimes in HH:mm format
            parsed_time = datetime.strptime(row_items[1], "%H:%M").time()

        row_data.append(
            {
                "time": datetime.combine(parsed_day, parsed_time, tzinfo=TIMEZONE),
                "total_generation": table_entry_to_float(row_items[2]),  # MW
                "total_demand": table_entry_to_float(row_items[3]),  # MW
                "loadshed": table_entry_to_float(row_items[4]),
                "gas": table_entry_to_float(row_items[5]),
                "oil": table_entry_to_float(row_items[6]),
                "coal": table_entry_to_float(row_items[7]),
                "hydro": table_entry_to_float(row_items[8]),
                "solar": table_entry_to_float(row_items[9]),
                "wind": table_entry_to_float(row_items[10]),
                "bd_import_bheramara": table_entry_to_float(row_items[11]),
                "bd_import_tripura": table_entry_to_float(row_items[12]),
                "remarks": row_items[13],
            }
        )

    return row_data


def verify_table_header(table_header: Tag):
    """
    Validate the table headers, that it looks like expected.
    Don't parse if the table has changed.
    """
    header_items = table_header.find_all("th")
    header_items = [item.text.strip() for item in header_items]

    if header_items != TABLE_HEADERS:
        raise ParserException(
            parser="BD.py",
            message=(
                f"Table headers mismatch with expected ones."
                f"Expected: {TABLE_HEADERS}"
                f"Parsed: {header_items}"
            ),
        )


def query(
    session: Session, target_datetime: datetime | None, logger: Logger
) -> list[dict[str, Any]]:
    """
    Query the table and read it into list.
    """
    # build URL to call
    if target_datetime is None:
        target_url = LATEST_URL
    else:
        # Convert timezone of target_datetime, and build URL from day
        target_datetime_bd = target_datetime.astimezone(TIMEZONE)
        target_dt_str = target_datetime_bd.strftime("%d-%m-%Y")
        target_url = HISTORICAL_URL + target_dt_str

    target_response: Response = session.get(target_url, verify=False)
    # SSL verification is disabled because the server's certificate is expired.

    if not target_response.ok:
        raise ParserException(
            parser="BD.py",
            message=f"Data request did not succeed: {target_response.status_code}",
        )

    response_soup = BeautifulSoup(target_response.text)

    # Find the table, there is only one, and verify its headers.
    table = response_soup.find("table")
    if table is None:
        raise ParserException(
            parser="BD.py",
            message="Could not find table in returned HTML.",
        )

    table_head = table.find("thead")
    if table_head is None:
        raise ParserException(
            parser="BD.py",
            message=("Could not find table header in returned HTML."),
        )
    verify_table_header(table_head)

    # Table valid as we expect, parse the rows.
    table_body = table.find("tbody")
    if table_body is None:
        raise ParserException(
            parser="BD.py",
            message=("Could not find table body in returned HTML."),
        )
    row_data = parse_table_body(table_body)

    return row_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "BD",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | list[dict[str, Any]]:
    row_data = query(session, target_datetime, logger)

    production_data_list = []
    for row in row_data:
        # Create data with empty production
        data = {
            "zoneKey": zone_key,
            "datetime": row["time"],
            "production": {},
            "source": "erp.pgcb.gov.bd",
        }

        # And add sources if they are present in the table
        known_sources_sum_mw = 0.0
        for source_type in ["coal", "gas", "hydro", "oil", "solar", "wind"]:
            if row[source_type] is not None:
                # also accumulate the sources to infer 'unknown'
                known_sources_sum_mw += row[source_type]
                data["production"][source_type] = row[source_type]

        # infer 'unknown'
        if row["total_generation"] is not None:
            unknown_source_mw = row["total_generation"] - known_sources_sum_mw
            if unknown_source_mw >= 0:
                data["production"]["unknown"] = unknown_source_mw
            else:
                logger.warn(
                    f"Sum of production sources exceeds total generation by {-unknown_source_mw}MW."
                    f"There is probably something wrong..."
                )

        production_data_list.append(data)

    if not len(production_data_list):
        raise ParserException(
            parser="BD.py",
            message="No valid consumption data for requested day found.",
        )
    return production_data_list


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("BD"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    row_data = query(session, target_datetime, logger)

    result_list = TotalConsumptionList(logger)

    for row in row_data:
        # get the demand from the table
        consumption = row["total_demand"]
        if consumption is None:
            continue  # no data in table

        result_list.append(
            zoneKey=zone_key,
            datetime=row["time"],
            consumption=consumption,
            source=SOURCE,
        )

    if not len(result_list):
        raise ParserException(
            parser="BD.py",
            message="No valid consumption data for requested day found.",
        )

    return result_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    # Query table, contains import from india.
    row_data = query(session, target_datetime, logger)

    result_list = []
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))

    for row in row_data:
        # BD -> IN_xx
        if zone_key2 == "IN-NE":
            # Export to India NorthEast via Tripura
            bd_import = row["bd_import_tripura"]
        elif zone_key2 == "IN-EA":
            # Export to India East via Bheramara
            bd_import = row["bd_import_bheramara"]
        else:
            raise ParserException(
                parser="BD.py",
                message=f"Exchange pair {sortedZoneKeys} is not implemented.",
            )

        if bd_import is None:
            continue  # no data in table
        bd_export = -1.0 * bd_import

        result_list.append(
            {
                "sortedZoneKeys": sortedZoneKeys,
                "datetime": row["time"],
                "netFlow": bd_export,
                "source": "erp.pgcb.gov.bd",
            }
        )

    return result_list


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_exchange('BD', 'IN-NE') ->")
    print(fetch_exchange("BD", "IN-NE"))
    print("fetch_exchange('BD', 'IN-EA') ->")
    print(fetch_exchange("BD", "IN-EA"))
