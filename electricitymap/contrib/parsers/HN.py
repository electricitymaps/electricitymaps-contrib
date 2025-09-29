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
from electricitymap.contrib.parsers.lib.exceptions import ParserException

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


def get_production_data_by_type(
    session: Session,
) -> list[tuple[list[Any], dict[str, str]]]:
    """
    Gets the production data from otr.ods.org.hn separated by plant type.
    Returns a list of tuples containing (CSV_data, plant_to_type_mapping) for each type.
    """
    data_by_type = []

    for index in range(1, 11):
        if index == 7:
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
        csv_data = []
        plant_to_type_map = {}

        for row in parsed_csv:
            if row[0] == "Fecha" or row[1] == "Planta":
                continue
            plant_to_type_map[row[1]] = INDEX_TO_TYPE_MAP[index]
            csv_data.append(row)

        if csv_data:
            data_by_type.append((csv_data, plant_to_type_map))

    return data_by_type


def get_exchange_data(session: Session) -> tuple[list[Any], dict[str, str]]:
    """
    Gets the exchange data from otr.ods.org.hn.
    Returns a tuple with CSV data and exchange mapping.
    """
    params = {
        "request": "CSV_N_",
        "p8_indx": 7,
    }
    response: Response = session.get(DATA_URL, params=params, verify=False)
    CSV_data = list(reader(response.text.splitlines()))
    return CSV_data, EXCHANGE_MAP


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


def create_production_breakdown_list(
    csv_data: list[Any], plant_to_type_map: dict[str, str], date: str, logger: Logger
) -> ProductionBreakdownList:
    """
    Create a ProductionBreakdownList from CSV data for a specific plant type.
    Uses ProductionMix.add_value() for automatic aggregation and validation.
    """
    breakdown_list = ProductionBreakdownList(logger)

    hourly_mixes = {hour: ProductionMix() for hour in range(24)}

    for row in csv_data:
        if not row or len(row) < 2 or row[1] not in plant_to_type_map:
            continue

        production_mode = plant_to_type_map[row[1]]
        hourly_values = row[2:]

        for hour, value in enumerate(hourly_values[:24]):
            float_value = safe_float_conversion(value)
            hourly_mixes[hour].add_value(production_mode, float_value)

    for hour, production_mix in hourly_mixes.items():
        dt = get_datetime(date, hour)
        if dt is not None:
            breakdown_list.append(
                zoneKey=ZoneKey("HN"),
                datetime=dt,
                source="ods.org.hn",
                production=production_mix,
            )

    return breakdown_list


def parse_exchange_data_by_hour(
    CSV_data: list, mapping: dict[str, str], date: str | None, logger: Logger
) -> dict[str, ExchangeList]:
    """
    Parse CSV data and return exchange lists by zone.
    Returns a dictionary with zone keys and ExchangeList values.
    """
    exchanges_by_zone = {}

    if date is None:
        return exchanges_by_zone

    for zone_key in mapping.values():
        exchanges_by_zone[zone_key] = ExchangeList(logger)

    for row in CSV_data:
        if not row or len(row) < 3 or row[1] not in mapping:
            continue

        zone_key = mapping[row[1]]
        direction_multiplier = EXCHANGE_DIRECTION_MAP[zone_key]
        hourly_values = row[2:]

        for hour, value in enumerate(hourly_values[:24]):
            float_value = safe_float_conversion(value)
            if float_value is not None:
                dt = get_datetime(date, hour)
                if dt is not None:
                    net_flow = float_value * direction_multiplier
                    exchanges_by_zone[zone_key].append(
                        zoneKey=ZoneKey(zone_key),
                        datetime=dt,
                        source="ods.org.hn",
                        netFlow=net_flow,
                    )

    return exchanges_by_zone


def get_production_values(
    data_by_type: list[tuple[list[Any], dict[str, str]]],
    logger: Logger,
) -> ProductionBreakdownList:
    """
    Gets the production values using the merge functionality to combine
    production breakdowns from different plant types.
    """
    if not data_by_type:
        return ProductionBreakdownList(logger)

    # Extract date from the first data source
    first_csv_data, _ = data_by_type[0]
    date = extract_date_from_csv(first_csv_data)

    if date is None:
        return ProductionBreakdownList(logger)

    production_breakdown_lists = []

    for csv_data, plant_to_type_map in data_by_type:
        if not csv_data:
            continue

        breakdown_list = create_production_breakdown_list(
            csv_data, plant_to_type_map, date, logger
        )

        if len(breakdown_list) > 0:
            production_breakdown_lists.append(breakdown_list)

    return ProductionBreakdownList.merge_production_breakdowns(
        production_breakdown_lists, logger
    )


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

    data_by_type = get_production_data_by_type(session)
    production_breakdowns = get_production_values(data_by_type, logger)

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

    CSV_data, EXCHANGE_MAP = get_exchange_data(session)
    date = extract_date_from_csv(CSV_data)
    exchanges_by_zone = parse_exchange_data_by_hour(
        CSV_data, EXCHANGE_MAP, date, logger
    )
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys in exchanges_by_zone:
        return exchanges_by_zone[sorted_zone_keys].to_list()
    else:
        return []
