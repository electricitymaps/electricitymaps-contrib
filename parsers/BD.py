#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import arrow
from bs4 import BeautifulSoup, Tag
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

# Power Grid Company of Bangladesh: erp.pgcb.gov.bd
# Has table (also historical) of production, consumption and exchange.
# This table gets updated batch-wise every few hours, so most of the time, the delay will be >2h.

tz = ZoneInfo("Asia/Dhaka")
latest_url = "https://erp.pgcb.gov.bd/web/generations/view_generations"
url_by_date = (
    "https://erp.pgcb.gov.bd/web/generations/view_generations?search="  # DD-MM-YYYY
)

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
    except ValueError:
        raise ParserException(
            parser="BD.py",
            message=(f'Failed to parse entry: "{entry}" to float in table.'),
        )


def parse_table_body(table_body: Tag):
    """
    Parse the table body returned by the URL.
    Returns a list of rows represented by dicts.
    """

    rows = table_body.find_all("tr")
    row_data = []

    for row in rows:
        row_items = row.find_all("td")
        row_items = [item.text.strip() for item in row_items]

        row_dict = dict()

        # date and time in [0]; [1] are DD-MM-YYYY; HH:mm[:ss]
        parsed_day = arrow.get(row_items[0], "DD-MM-YYYY", tzinfo=tz).datetime
        try:
            parsed_time = arrow.get(row_items[1], "HH:mm:ss", tzinfo=tz).time()
        except arrow.parser.ParserMatchError:
            # very old data points are sometimes in HH:mm format
            parsed_time = arrow.get(row_items[1], "HH:mm", tzinfo=tz).time()

        row_dict["time"] = datetime.combine(parsed_day, parsed_time, tzinfo=tz)

        # [2] is total generation in MW
        row_dict["total_generation"] = table_entry_to_float(row_items[2])
        # [3] is total demand in MW
        row_dict["total_demand"] = table_entry_to_float(row_items[3])
        # [4] is loadshed, not interesting for us
        row_dict["loadshed"] = table_entry_to_float(row_items[4])
        # [5] is generation from gas
        row_dict["gas"] = table_entry_to_float(row_items[5])
        # [6] is generation from liquid fuel (oil)
        row_dict["oil"] = table_entry_to_float(row_items[6])
        # [7] is generation from coal
        row_dict["coal"] = table_entry_to_float(row_items[7])
        # [8] is generation from hydro
        row_dict["hydro"] = table_entry_to_float(row_items[8])
        # [9] is generation from solar
        row_dict["solar"] = table_entry_to_float(row_items[9])
        # [10] is generation from wind
        row_dict["wind"] = table_entry_to_float(row_items[10])
        # [11], [12] is import from Bheramara PP (IN-EA) and Tripura (IN-NE)
        row_dict["bd_import_bheramara"] = table_entry_to_float(row_items[11])
        row_dict["bd_import_tripura"] = table_entry_to_float(row_items[12])
        row_dict["remarks"] = row_items[13]

        row_data.append(row_dict)

    return row_data


def verify_table(table_header: Tag):
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
        target_url = latest_url
    else:
        # Convert timezone of target_datetime, and build URL from day
        target_datetime_bd = arrow.get(target_datetime).to(tz)
        target_dt_str = target_datetime_bd.format("DD-MM-YYYY")
        target_url = url_by_date + target_dt_str

    target_response: Response = session.get(target_url)

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
    verify_table(table_head)

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
    zone_key: str = "BD",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | list[dict[str, Any]]:
    row_data = query(session, target_datetime, logger)

    result_list = []

    for row in row_data:
        # get the demand from the table
        consumption = row["total_demand"]
        if consumption is None:
            continue  # no data in table

        result_list.append(
            {
                "datetime": row["time"],
                "consumption": consumption,
                "zoneKey": zone_key,
                "source": "erp.pgcb.gov.bd",
            }
        )

    if not len(result_list):
        raise ParserException(
            parser="BD.py",
            message="No valid consumption data for requested day found.",
        )

    return result_list


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
