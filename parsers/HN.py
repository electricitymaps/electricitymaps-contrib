from csv import reader
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

DATA_URL = "https://otr.ods.org.hn:3200/odsprd/ods_prd/r/operador-del-sistema-ods/producci%C3%B3n-horaria"

INDEX_TO_TYPE_MAP = {
    1: "hydro",
    2: "wind",
    3: "solar",
    4: "geothermal",
    5: "biomass",
    6: "coal",
    # 7: Exchanges
    8: "oil",
    9: "oil",
    10: "hydro",
}

EXCHANGE_MAP = {
    "Guatemala": "GT->HN",
    "Nicaragua": "HN->NI",
    "El Salvador": "HN->SV",
}

EXCHANGE_DIRECTION_MAP = {
    "GT->HN": -1,
    "HN->NI": 1,
    "HN->SV": 1,
}


def get_data(
    session: Session, data_type: str = "production"
) -> tuple[list[Any], dict[str, str]]:
    """
    Gets the data from otr.ods.org.hn and returns it as a list with
    the data and a dictionary with the plant to type mapping or an exchange mapping.
    """
    CSV_data = []
    PLANT_TO_TYPE_MAP = {}
    if data_type == "production":
        for index in range(1, 11):
            if index == 7:  # Skip exchanges
                continue
            params = {
                "request": "CSV_N_",
                "p8_indx": index,
            }
            response: Response = session.get(
                DATA_URL,
                params=params,
                verify=False,
            )

            parsed_csv = list(reader(response.text.splitlines()))
            for row in parsed_csv:
                if row[0] == "Fecha" or row[1] == "Planta":
                    continue
                PLANT_TO_TYPE_MAP[row[1]] = INDEX_TO_TYPE_MAP[index]
                CSV_data.append(row)
        return CSV_data, PLANT_TO_TYPE_MAP
    elif data_type == "exchange":
        params = {
            "request": "CSV_N_",
            "p8_indx": 7,
        }
        response: Response = session.get(DATA_URL, params=params, verify=False)
        CSV_data = list(reader(response.text.splitlines()))
        return CSV_data, EXCHANGE_MAP
    else:
        raise ParserException("HN.py", f"Invalid data type: {data_type}")


def safe_float_conversion(value: str | None) -> float | None:
    """
    Safely converts a string value to float, returning None for missing or empty values.
    """
    if value is None or value == "" or value.strip() == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def extract_date_from_csv(CSV_data: list) -> str | None:
    """
    Extracts the date from the CSV data
    """
    for row in CSV_data:
        if row and len(row) > 0 and row[0] != "Fecha":
            return row[0]
    return None


def parse_production_data_by_hour(
    CSV_data: list, mapping: dict[str, str]
) -> dict[int, ProductionMix]:
    """
    Parse CSV data and group production values by hour.
    Returns a dictionary with hour as key and ProductionMix as values.
    """
    values_by_hour = {i: ProductionMix() for i in range(0, 24)}

    for row in CSV_data:
        # Skip empty or malformed rows
        if not row or len(row) < 2:
            continue

        if len(row) < 2 or row[1] == "Planta":
            continue

        # Check if plant name exists in mapping
        if row[1] not in mapping:
            continue

        row_values_by_hour = row[2:] if len(row) > 2 else []
        index = 0
        for value in row_values_by_hour:
            if row[0] == "Fecha":
                continue
            # Ensure we don't exceed 24 hours
            if index >= 24:
                break

            float_value = safe_float_conversion(value)
            mode = mapping[row[1]]

            # Use ProductionMix.add_value() which handles None safely and sums automatically
            values_by_hour[index].add_value(mode, float_value, correct_negative_with_zero=True)

            index += 1

    return values_by_hour


def parse_exchange_data_by_hour(
    CSV_data: list, mapping: dict[str, str]
) -> dict[int, dict[str, float | None]]:
    """
    Parse CSV data and group exchange values by hour.
    Returns a dictionary with hour as key and {zone: net_flow} as values.
    """
    values_by_hour = {i: {} for i in range(0, 24)}

    for row in CSV_data:
        # Skip empty or malformed rows
        if not row or len(row) < 2:
            continue

        if len(row) < 2 or row[1] == "Planta":
            continue

        # Check if plant name exists in mapping
        if row[1] not in mapping:
            continue

        row_values_by_hour = row[2:] if len(row) > 2 else []
        index = 0
        for value in row_values_by_hour:
            if row[0] == "Fecha":
                continue
            # Ensure we don't exceed 24 hours
            if index >= 24:
                break

            float_value = safe_float_conversion(value)
            zone = mapping[row[1]]

            if float_value is None:
                values_by_hour[index][zone] = None
            else:
                # Apply direction multiplier for exchanges
                net_flow = float_value * EXCHANGE_DIRECTION_MAP[zone]
                if zone in values_by_hour[index]:
                    current_value = values_by_hour[index][zone]
                    if current_value is not None:
                        values_by_hour[index][zone] = current_value + net_flow
                    else:
                        values_by_hour[index][zone] = net_flow
                else:
                    values_by_hour[index][zone] = net_flow

            index += 1

    return values_by_hour


def get_exchange_values(
    CSV_data: list, mapping: dict, date: str | None, logger: Logger
) -> dict[str, ExchangeList]:
    """
    Gets the exchange values from the CSV data and returns a dictionary of ExchangeLists by zone key
    """
    exchanges_by_zone = {}
    if date is None:
        return exchanges_by_zone

    values_by_hour = parse_exchange_data_by_hour(CSV_data, mapping)

    # Create Exchange events for each hour and zone
    for hour in range(24):
        hour_exchanges = values_by_hour[hour]
        if hour_exchanges:  # Only create if there's data
            dt = get_datetime(date, hour)
            if dt is not None:
                for zone_key, net_flow in hour_exchanges.items():
                    if zone_key not in exchanges_by_zone:
                        exchanges_by_zone[zone_key] = ExchangeList(logger)

                    exchanges_by_zone[zone_key].append(
                        zoneKey=ZoneKey(zone_key),
                        datetime=dt,
                        source="ods.org.hn",
                        netFlow=net_flow,
                    )

    return exchanges_by_zone


def get_production_values(
    CSV_data: list, mapping: dict, date: str | None, logger: Logger
) -> ProductionBreakdownList:
    """
    Gets the production values from the CSV data and returns a ProductionBreakdownList
    """
    production_breakdowns = ProductionBreakdownList(logger)
    if date is None:
        return production_breakdowns

    values_by_hour = parse_production_data_by_hour(CSV_data, mapping)

    # Create ProductionBreakdown events for each hour
    for hour in range(24):
        production_mix = values_by_hour[hour]
        dt = get_datetime(date, hour)
        if dt is not None and isinstance(production_mix, ProductionMix):
            # Skip hours with completely empty production mix
            if all(value is None for value in production_mix.dict().values()):
                continue

            production_breakdowns.append(
                zoneKey=ZoneKey("HN"),
                datetime=dt,
                source="ods.org.hn",
                production=production_mix,
            )

    return production_breakdowns


def get_datetime(date: str | None, hour: int) -> datetime | None:
    """
    Returns a datetime object with the given date and hour, or None if date is invalid
    """
    if date is None or date == "" or date.strip() == "":
        return None
    try:
        return datetime.strptime(date, "%m/%d/%Y").replace(
            tzinfo=ZoneInfo("America/Tegucigalpa")
        ) + timedelta(hours=hour)
    except (ValueError, TypeError):
        return None


def fetch_production(
    zone_key: str = "HN",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is not None:
        raise ParserException(
            "HN.py", "This parser is not yet able to parse past dates"
        )

    CSV_data, PLANT_TO_TYPE_MAP = get_data(session, "production")
    date = extract_date_from_csv(CSV_data)
    production_breakdowns = get_production_values(
        CSV_data, PLANT_TO_TYPE_MAP, date, logger
    )

    return production_breakdowns.to_list()


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is not None:
        raise ParserException(
            "HN.py", "This parser is not yet able to parse past dates"
        )

    CSV_data, EXCHANGE_MAP = get_data(session, "exchange")
    date = extract_date_from_csv(CSV_data)
    exchanges_by_zone = get_exchange_values(CSV_data, EXCHANGE_MAP, date, logger)
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys in exchanges_by_zone:
        return exchanges_by_zone[sorted_zone_keys].to_list()
    else:
        return []
