import io
import logging
import re
from collections.abc import Callable
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pdfplumber
import requests
from requests import Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import ExchangeList
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"
HOST = "https://app.erldc.in"
GRID_INDIA_BACKEND_API = "https://webapi.grid-india.in/api/v1/file"
INTERNATIONAL_EXCHANGES_URL = "{proxy}/api/pspreportpsp/Get/pspreport_psp_transnationalexchange/GetByTwoDate?host={host}&firstDate={target_date}&secondDate={target_date}"
INTERREGIONAL_EXCHANGES_URL = "{proxy}/api/pspreportpsp/Get/pspreport_psp_interregionalexchanges/GetByTwoDate?host={host}&firstDate={target_date}&secondDate={target_date}"
GRID_INDIA_URL = "{proxy}/reports/daily-psp-report?host={host}"
GRID_INDIA_URL_WITHOUT_PROXY = "https://grid-india.in/reports/daily-psp-report"
GRID_INDIA_CDN_WITHOUT_PROXY = "https://webcdn.grid-india.in"
IN_EA_TZ = ZoneInfo("Asia/Kolkata")

SOURCE = "grid-india.in"

# 1MU = 1 GWH = 1000 MWH then assume uniform production per hour -> 1000/24 = 41.6666 = 1/0.024
CONVERSION_MU_MW = 0.024


def get_psp_report_file_url(target_date: datetime) -> str:
    """
    Scrapes the Grid India PSP report page to find downloadable files.
    Returns a list of dictionaries containing file information.
    """

    # url = GRID_INDIA_URL.format(proxy=IN_WE_PROXY, host=HOST_GRID_INDIA)
    url = GRID_INDIA_BACKEND_API
    target_date_filename_format = "%d.%m.%y"
    target_date_filename = target_date.strftime(target_date_filename_format)

    try:
        response = requests.post(
            url,
            json={
                "_source": "GRDW",
                "_type": "DAILY_PSP_REPORT",
                "_fileDate": "",
                "_month": "00",
            },
        )

        response.raise_for_status()
        all_files = response.json().get("retData")

        file_patterns = [
            f"{target_date_filename}_NLDC_PSP_(\d)+.pdf",  # After approx May 1, 2025
            f"{target_date_filename}_NLDC_PSP.pdf",  # Before approx May 1, 2025
        ]

        for file_regex in file_patterns:
            file_for_target_date = [
                item for item in all_files if re.search(file_regex, item["FilePath"])
            ]

            if len(file_for_target_date) > 1:
                logger.error(f"Multiple files found for {target_date_filename}")
                raise ParserException(
                    parser="IN_EA.py",
                    message=f"{target_date}: Multiple files found for {target_date_filename}",
                )

            if file_for_target_date:
                return f"{GRID_INDIA_CDN_WITHOUT_PROXY}/{file_for_target_date[0]['FilePath']}"

            else:
                continue

        raise ParserException(
            parser="IN_EA.py",
            message=f"No file found for {target_date}. Some dates may not have a PSP report.",
        )

    except requests.RequestException as e:
        raise ParserException(
            parser="IN_EA.py",
            message=f"{target_date}: Error fetching the webpage: {e}",
        ) from e
    except Exception as e:
        raise ParserException(
            parser="IN_EA.py",
            message=f"{target_date}: Error parsing the webpage: {e}",
        ) from e


def find_table_after_text(pdf, heading_text) -> list[list[str]]:
    """
    Searches for a specific text heading and extracts the first table found immediately after it.
    This relies on the visual layout of the PDF.

    Args:
        pdf (pdfplumber.PDF): An opened pdfplumber PDF object.
        heading_text (str): The text of the heading to search for.

    Returns:
        A list of lists representing the found table, or None if not found.
    """
    for page in pdf.pages:
        # Search for the heading text on the page (case-insensitive)
        search_results = page.search(heading_text, case=False)

        if search_results:
            # We found the heading. Use the first match's coordinates.
            heading_bbox = search_results[0]
            heading_bottom = heading_bbox[
                "bottom"
            ]  # The y-coordinate of the bottom of the heading

            logging.info(f"Found '{heading_text}' heading on page {page.page_number}.")

            # Define a bounding box for the area *below* the heading to the bottom of the page
            page_crop_bbox = (0, heading_bottom, page.width, page.height)

            # Create a virtual crop of the page
            cropped_page = page.crop(bbox=page_crop_bbox)

            logging.info(
                "Searching for table in the area immediately below the heading."
            )

            # Extract the first table found in this cropped area
            table = cropped_page.extract_table()

            if table:
                logging.info("Successfully extracted table from the designated area.")
                return table
            else:
                raise ParserException(
                    parser="IN_EA.py",
                    message=f"Found heading on page {page.page_number}, but no table was found directly below it.",
                    zone_key=ZoneKey("IN-EA"),
                )
    raise ParserException(
        parser="IN_EA.py",
        message=f"Could not find the heading '{heading_text}' anywhere in the PDF.",
        zone_key=ZoneKey("IN-EA"),
    )


def find_and_extract_table(pdf, table_header_text):
    """
    Searches for a table with a specific header text within a PDF.

    Args:
        pdf (pdfplumber.PDF): An opened pdfplumber PDF object.
        table_header_text (str): The text to identify the target table's header row.

    Returns:
        A list of lists representing the found table, or None if not found.
    """
    for page in pdf.pages:
        # Extract all tables from the current page
        tables = page.extract_tables()
        for table in tables:
            # Check if the first row of the table contains the header we're looking for
            if table and table[0] and table_header_text in table[0][0]:
                logging.info(
                    f"Found '{table_header_text}' table on page {page.page_number}."
                )
                return table
    return None


def find_and_set_header(df, search_keywords=("sl no",)):
    """
    Searches for a header row containing in the DataFrame that contains "sl no".
    Some years the header is not the first row, so we search the first 10 rows.

    Args:
        df (pd.DataFrame): The DataFrame to search.
        search_keywords (tuple): A tuple of keywords to look for in the header row.

    Returns:
        pd.DataFrame: The DataFrame with the header row set if found.
    """

    for i in range(min(10, len(df))):
        row = df.iloc[i]
        cleaned_row = row.astype(str).str.replace(r"\s+", " ", regex=True).str.lower()

        if any(
            any(keyword in cell for cell in cleaned_row) for keyword in search_keywords
        ):
            df.columns = row
            df = df.iloc[i + 1 :].reset_index(drop=True)

            df.columns = [
                str(col).replace("\n", " ").strip() for col in df.columns
            ]  # For some dates the column names have \n
            return df

    raise ValueError("Could not find header row with expected keywords.")


def parse_pdf_for_interregional_exchanges(
    pdf_url: str, zone_key: ZoneKey
) -> dict[ZoneKey, float]:
    """
    Parses the PDF content and returns a dictionary of interregional exchanges.
    """
    response = requests.get(pdf_url)
    response.raise_for_status()

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        target_table_data = find_table_after_text(pdf, "Inter-Regional Exchanges")

        df = pd.DataFrame(target_table_data)
        df = find_and_set_header(df, search_keywords=("sl no",))

        cols_to_keep = [
            col for col in df.columns if "sl no" in col.lower() or "net" in col.lower()
        ]

        df = df[cols_to_keep].rename(
            columns={cols_to_keep[0]: "zone_key", cols_to_keep[1]: "net_flow"}
        )

        df = df[df["zone_key"] == INTERREGIONAL_EXCHANGES_MAPPING[zone_key]]

        if len(df) > 1:
            raise ParserException(
                parser="IN_EA.py",
                message=f"Multiple rows found for {zone_key} while we only expect to find one daily value",
                zone_key=zone_key,
            )
        try:
            net_flow_mu = float(df["net_flow"].iloc[0])
            if zone_key in REVERSED_INTERREGIONAL_EXCHANGES:
                net_flow_mu = -net_flow_mu

            return {zone_key: round(net_flow_mu / CONVERSION_MU_MW, 3)}

        except Exception as e:
            raise ParserException(
                parser="IN_EA.py",
                message=f"Could not find a valid value for {zone_key} for {pdf_url}: {e}",
                zone_key=zone_key,
            ) from e


def parse_pdf_for_international_exchanges(
    pdf_url: str, zone_key: ZoneKey
) -> dict[ZoneKey, float]:
    """
    Parses the PDF content and returns a dictionary of international exchanges.
    """
    response = requests.get(pdf_url)
    response.raise_for_status()

    with pdfplumber.open(io.BytesIO(response.content)) as pdf:
        target_table_data = find_table_after_text(pdf, "International Exchanges")

        df = pd.DataFrame(target_table_data)
        df = find_and_set_header(df, search_keywords=("state",))
        df["State"] = df["State"].ffill()

        cols_to_keep = [
            col
            for col in df.columns
            if "state" in col.lower()
            or "region" in col.lower()
            or "(mu)" in col.lower()
        ]

        if len(cols_to_keep) != 3:
            raise ParserException(
                parser="IN_EA.py",
                message=f"Needed columns not found or too many found in table for {zone_key}",
                zone_key=zone_key,
            )

        df["zone_key"] = df[[cols_to_keep[0], cols_to_keep[1]]].agg("-".join, axis=1)

        df = df[["zone_key", cols_to_keep[2]]].rename(
            columns={
                cols_to_keep[2]: "net_flow",
            }
        )

        df = df[df["zone_key"] == INTERNATIONAL_EXCHANGES_MAPPING[zone_key]]
        df["net_flow"] = df["net_flow"].astype(float)
        df = df.groupby("zone_key").sum()

        try:
            net_flow_mu = df["net_flow"].iloc[0]
            if zone_key in REVERSED_INTERNATIONAL_EXCHANGES:
                net_flow_mu = -net_flow_mu
            print(net_flow_mu)
            return {zone_key: round(net_flow_mu / CONVERSION_MU_MW, 3)}

        except Exception as e:
            raise ParserException(
                parser="IN_EA.py",
                message=f"Could not find a valid value for {zone_key} for {pdf_url}: {e}",
                zone_key=zone_key,
            ) from e


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """collects average daily exchanges from Grid India"""
    logging.getLogger("pdfminer").setLevel(logging.WARNING)

    if target_datetime is None:
        # 1 day delay observed
        target_datetime = datetime.now(tz=IN_EA_TZ).replace(
            hour=0, minute=0, second=0
        ) - timedelta(days=1)

    else:
        target_datetime = target_datetime.astimezone(IN_EA_TZ).replace(
            hour=0, minute=0, second=0
        )

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    exchange_list = ExchangeList(logger)
    file_url = get_psp_report_file_url(target_datetime)
    print(file_url)

    if sorted_zone_keys in INTERREGIONAL_EXCHANGES_MAPPING:
        exchange_data = parse_pdf_for_interregional_exchanges(
            file_url, sorted_zone_keys
        )

    elif sorted_zone_keys in INTERRNATIONAL_EXCHANGES:
        exchange_data = parse_pdf_for_international_exchanges(
            file_url, sorted_zone_keys
        )

    exchange_list.append(
        zoneKey=sorted_zone_keys,
        datetime=target_datetime,
        netFlow=exchange_data.get(sorted_zone_keys),
        source=SOURCE,
    )
    return exchange_list.to_list()


INTERREGIONAL_EXCHANGES_MAPPING = {
    ZoneKey("IN-EA->IN-NO"): "ER-NR",
    ZoneKey("IN-EA->IN-NE"): "ER-NER",
    ZoneKey("IN-EA->IN-SO"): "ER-SR",
    ZoneKey("IN-EA->IN-WE"): "ER-WR",
    ZoneKey("IN-NO->IN-WE"): "WR-NR",  # Reversed exchange
    ZoneKey("IN-SO->IN-WE"): "WR-SR",  # Reversed exchange
    ZoneKey("IN-NE->IN-NO"): "NER-NR",
}

INTERNATIONAL_EXCHANGES_MAPPING = {
    ZoneKey("BT->IN-EA"): "BHUTAN-ER",
    ZoneKey("BT->IN-NE"): "BHUTAN-NER",
    ZoneKey("IN-EA->NP"): "NEPAL-ER",
    ZoneKey("IN-NO->NP"): "NEPAL-NR",
    ZoneKey("BD->IN-EA"): "BANGLADESH-ER",
    ZoneKey("BD->IN-NE"): "BANGLADESH-NER",
}

REVERSED_INTERREGIONAL_EXCHANGES = ["IN-NO->IN-WE", "IN-SO->IN-WE"]

REVERSED_INTERNATIONAL_EXCHANGES = ["IN-EA->NP", "IN-NO->NP"]

INTERREGIONAL_EXCHANGES = {
    ZoneKey("IN-EA->IN-NO"): "Import/Export between EAST REGION and NORTH REGION",
    ZoneKey("IN-EA->IN-NE"): "Import/Export between EAST REGION and NORTH_EAST REGION",
    ZoneKey("IN-EA->IN-SO"): "Import/Export between EAST REGION and SOUTH REGION",
    ZoneKey("IN-EA->IN-WE"): "Import/Export between EAST REGION and WEST REGION",
}
INTERRNATIONAL_EXCHANGES = {
    ZoneKey("BT->IN-EA"): "BHUTAN",
    ZoneKey("IN-EA->NP"): "NEPAL",
    ZoneKey("BD->IN-EA"): "BANGLADESH",
}

MAPPING = {
    **INTERREGIONAL_EXCHANGES,
    **INTERRNATIONAL_EXCHANGES,
}


def get_fetch_function(
    exchange_key: ZoneKey,
) -> tuple[str, Callable[[list, ZoneKey, Logger], ExchangeList]]:
    """Get the url, the lookup key and the extract function for the exchange."""
    if exchange_key not in MAPPING:
        raise ParserException(
            "IN_EA.py",
            f"Unsupported exchange key {exchange_key}",
            zone_key=exchange_key,
        )
    if exchange_key in INTERRNATIONAL_EXCHANGES:
        return (
            INTERNATIONAL_EXCHANGES_URL,
            extract_international_exchanges,
        )
    return (
        INTERREGIONAL_EXCHANGES_URL,
        extract_interregional_exchanges,
    )


def extract_international_exchanges(
    raw_data: list, exchange_key: ZoneKey, logger: Logger
) -> ExchangeList:
    exchanges = ExchangeList(logger)
    zone_data = [item for item in raw_data if item["Region"] == MAPPING[exchange_key]][
        0
    ]
    exchanges.append(
        zoneKey=exchange_key,
        datetime=datetime.strptime(zone_data["Date"], "%Y-%m-%d").replace(
            tzinfo=IN_EA_TZ
        ),
        netFlow=float(zone_data["DayAverageMW"]),
        source="erldc.in",
    )
    return exchanges


def extract_interregional_exchanges(
    raw_data: list, exchange_key: ZoneKey, logger: Logger
) -> ExchangeList:
    exchanges = ExchangeList(logger)
    zone_data = [item for item in raw_data if item["Type"] == MAPPING[exchange_key]]
    imports = sum(float(item["ImportMW"]) for item in zone_data)
    exports = sum(float(item["ExportMW"]) for item in zone_data)  # always negative
    exchanges.append(
        zoneKey=exchange_key,
        datetime=datetime.strptime(zone_data[0]["Date"], "%Y-%m-%d").replace(
            tzinfo=IN_EA_TZ
        ),
        netFlow=imports + exports,
        source="erldc.in",
    )
    return exchanges


if __name__ == "__main__":
    logger = logging.getLogger(__name__)

    file_url = get_psp_report_file_url(datetime(2025, 6, 12, tzinfo=IN_EA_TZ))

    parsed_data = parse_pdf_for_interregional_exchanges(
        file_url, zone_key=ZoneKey("IN-EA->IN-NE")
    )
    print(parsed_data)
