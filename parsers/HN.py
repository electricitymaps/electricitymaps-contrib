from csv import reader
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional, Tuple, Union

from pytz import timezone
from requests import Response, Session

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
    session: Session, type: str = "production"
) -> Tuple[List[Any], Dict[str, str]]:
    """
    Gets the data from otr.ods.org.hn and returns it as a list with
    the data and a dictionary with the plant to type mapping or an exchange mapping.
    """
    CSV_data = []
    PLANT_TO_TYPE_MAP = {}
    if type == "production":
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
    elif type == "exchange":
        params = {
            "request": "CSV_N_",
            "p8_indx": 7,
        }
        response: Response = session.get(DATA_URL, params=params, verify=False)
        CSV_data = list(reader(response.text.splitlines()))
        return CSV_data, EXCHANGE_MAP
    else:
        raise ParserException("HN.py", f"Invalid data type: {type}")


def format_values(
    values_by_hour: Dict[int, Any],
    mapping: dict,
    value: str,
    kind: str,
    id: str,
    index: int,
):
    if kind == "production":
        if mapping[id] in values_by_hour[index].keys():
            values_by_hour[index][mapping[id]] += (
                float(value) if float(value) > 0 else 0
            )
        else:
            values_by_hour[index][mapping[id]] = float(value) if float(value) > 0 else 0
    elif kind == "exchange":
        values_by_hour[index][mapping[id]] = (
            float(value) * EXCHANGE_DIRECTION_MAP[mapping[id]]
        )
    else:
        raise ParserException("HN.py", f"Invalid data type: {kind}")
    return values_by_hour


def get_values(CSV_data: list, mapping: dict, kind: str = "production"):
    """
    Gets the values from the CSV data and returns a dictionary with the values by hour and the date
    """
    values_by_hour = {i: {} for i in range(0, 24)}
    date: Union[str, None] = None
    for row in CSV_data:
        if date is None:
            date = row[0] if row[0] != "Fecha" else None
        if row[1] == "Planta":
            continue
        row_production_by_hour = row[2:]
        index = 0
        for value in row_production_by_hour:
            if row[0] == "Fecha":
                continue
            if value != "":
                values_by_hour = format_values(
                    values_by_hour=values_by_hour,
                    mapping=mapping,
                    value=value,
                    kind=kind,
                    id=row[1],
                    index=index,
                )
            index += 1
    return values_by_hour, date


def get_datetime(date: str, hour: int) -> datetime:
    """
    Returns a datetime object with the given date and hour
    """
    return datetime.strptime(date, "%m/%d/%Y").replace(
        tzinfo=timezone("America/Tegucigalpa")
    ) + timedelta(hours=hour + 1)


def fetch_production(
    zone_key: str = "HN",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is not None:
        raise ParserException(
            "HN.py", "This parser is not yet able to parse past dates"
        )

    CSV_data, PLANT_TO_TYPE_MAP = get_data(session, "production")
    production_by_hour, date = get_values(CSV_data, PLANT_TO_TYPE_MAP)

    production_list = []
    if date is not None:
        for index in range(0, 24):
            if production_by_hour[index] != {}:
                production_list.append(
                    {
                        "zoneKey": zone_key,
                        "datetime": get_datetime(date, index),
                        "production": production_by_hour[index],
                        "source": "ods.org.hn",
                    }
                )

    return production_list


def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime is not None:
        raise ParserException(
            "HN.py", "This parser is not yet able to parse past dates"
        )

    CSV_data, EXCHANGE_MAP = get_data(session, "exchange")
    exchange_per_hour, date = get_values(CSV_data, EXCHANGE_MAP, "exchange")
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    exchange_list = []
    if date is not None:
        for index in range(0, 24):
            if exchange_per_hour[index] != {}:
                exchange_list.append(
                    {
                        "sortedZoneKeys": sorted_zone_keys,
                        "datetime": get_datetime(date, index),
                        "netFlow": exchange_per_hour[index][sorted_zone_keys],
                        "source": "ods.org.hn",
                    }
                )

    return exchange_list
