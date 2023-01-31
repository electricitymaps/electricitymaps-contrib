from csv import reader
from datetime import datetime, timedelta
from logging import getLogger
from typing import Union

from pytz import timezone
from requests import Response, Session

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


def fetch_production(
    zone_key="HN",
    session=Session(),
    target_datetime=None,
    logger=getLogger(__name__),
):
    production_list = []
    CSV_data = []
    PLANT_TO_TYPE_MAP = {}

    for index in range(1, 11):
        if index == 7:  # Skip exchanges
            continue
        params = {
            "request": "CSV_N_",
            "p8_indx": index,
        }
        response: Response = session.get(
            "https://otr.ods.org.hn:3200/odsprd/ods_prd/r/operador-del-sistema-ods/producci%C3%B3n-horaria",
            params=params,
            verify=False,
        )
        csv_file = response.text
        parsed_csv = list(reader(csv_file.splitlines()))
        for row in parsed_csv:
            if row[0] == "Fecha" or row[1] == "Planta":
                continue
            PLANT_TO_TYPE_MAP[row[1]] = INDEX_TO_TYPE_MAP[index]
        CSV_data.append(parsed_csv)

    # Flatten the CSV_data list
    CSV_data = [item for sublist in CSV_data for item in sublist]

    production_by_hour = {}
    for index in range(0, 24):
        production_by_hour[index] = {}

    date: Union[str, None] = None
    for row in CSV_data:
        if date is None:
            date = row[0] if row[0] != "Fecha" else None
        if row[1] == "Planta":
            continue
        plant_production_by_hour = row[2:]
        index = 0
        for production in plant_production_by_hour:
            if row[0] == "Fecha":
                continue
            if (
                PLANT_TO_TYPE_MAP[row[1]] in production_by_hour[index].keys()
                and production != ""
            ):
                production_by_hour[index][PLANT_TO_TYPE_MAP[row[1]]] += (
                    float(production) if float(production) > 0 else 0
                )
            elif production != "":
                production_by_hour[index][PLANT_TO_TYPE_MAP[row[1]]] = (
                    float(production) if float(production) > 0 else 0
                )
            index += 1
    if date is not None:
        for index in range(0, 24):
            production_datetime = datetime.strptime(date, "%m/%d/%Y")
            production_datetime = production_datetime.replace(
                tzinfo=timezone("America/Tegucigalpa")
            ) + timedelta(hours=index + 1)
            if production_by_hour[index] != {}:
                production_list.append(
                    {
                        "zoneKey": zone_key,
                        "datetime": production_datetime,
                        "production": production_by_hour[index],
                        "source": "ods.org.hn",
                    }
                )

    return production_list
