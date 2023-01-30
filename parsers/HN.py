from csv import reader
from requests import Response, Session


def fetch_production(
    zone_key="HN",
    session=Session(),
    target_datetime=None,
    logger=None,
):
    production_list = []
    params = {
        "request": "CSV_N_",
    }

    response: Response = session.get(
        "https://otr.ods.org.hn:3200/odsprd/ods_prd/r/operador-del-sistema-ods/producci%C3%B3n-horaria",
        params=params,
        verify=False,
    )
    csv_file = response.text
    parsed_csv = reader(csv_file.splitlines())
    for row in parsed_csv:
        data = {
            "date": row[0],
            "power_plant": row[1],
            "production_per_hour": [None if x == "" else float(x) for x in row[2:]],
        }
        plant_production_list = []
        for i, production in enumerate(data["production_per_hour"]):
            plant_production_list.append(
                {
                    "power_plant": data["power_plant"],
                    "date": data["date"],
                    "hour": i + 1,
                    "production": production,
                }
            )
        print(plant_production_list)

    return production_list
