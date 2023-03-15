#!/usr/bin/env python3
import json
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Session

#   PARSER FOR COLOMBIA / DEMAND-ONLY as of 2023-02-11 / 5-minute-granularity / returns demand data of the recent day
#   MAIN_WEBSITE = https://www.xm.com.co/consumo/demanda-en-tiempo-real
colombia_demand_URL = "https://serviciosfacturacion.xm.com.co/XM.Portal.Indicadores/api/Operacion/DemandaTiempoReal"

TZ = "America/Bogota"  # UTC-5
demand_list = []


def fetch_consumption(
    zone_key: str = "CO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates.")
    with session.get(colombia_demand_URL, verify=False) as response:
        demand_json = json.loads(response.content)
        demand_data = demand_json["Variables"][0]["Datos"]

        for datapoint in demand_data:
            demand_list.append(
                {
                    "zoneKey": zone_key,
                    "datetime": arrow.get(datapoint["Fecha"], tzinfo=TZ).datetime,
                    "consumption": round(datapoint["Valor"], 1),
                    "source": "xm.com.co",
                }
            )

    return demand_list


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
