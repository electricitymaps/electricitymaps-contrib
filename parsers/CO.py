#!/usr/bin/env python3
import json
from datetime import datetime, time, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
from pydataxm import pydataxm
from requests import Session

from .lib.config import refetch_frequency

#   PARSER FOR COLOMBIA / DEMAND-ONLY as of 2023-02-11 / 5-minute-granularity / returns demand data of the recent day
#   MAIN_WEBSITE = https://www.xm.com.co/consumo/demanda-en-tiempo-real
colombia_demand_URL = "https://serviciosfacturacion.xm.com.co/XM.Portal.Indicadores/api/Operacion/DemandaTiempoReal"

TZ = "America/Bogota"  # UTC-5
demand_list = []

# dictionnary of plant types XM to EMaps https://www.xm.com.co/generacion/tipos
TYPES_XM_EM = {
    "AGUA": "hydro",
    "BIOGAS": "biomass",
    "CARBON": "coal",
    "GAS": "gas",
    "BAGAZO": "biomass",
    "RAD SOLAR": "solar",
    "VIENTO": "wind",
    "COMBUSTOLEO": "oil",
    "ACPM": "oil",
    "JET-A1": "oil",
}


def fetch_consumption(
    zone_key: str = "CO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if target_datetime:
        return fetch_historical_consumption(zone_key, session, target_datetime, logger)
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


@refetch_frequency(timedelta(days=1))
def fetch_historical_consumption(
    zone_key: str = "CO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    # Convert datetime to local time
    co_datetime = arrow.get(target_datetime).to(TZ)

    objetoAPI = pydataxm.ReadDB()

    # API request consumption
    df_consumption = objetoAPI.request_data(
        "DemaReal", "Sistema", co_datetime.date(), co_datetime.date()
    )
    if df_consumption.empty:
        return []

    else:
        # Select the columns with the consumption values for each hours
        df_consumption = df_consumption.iloc[:, 2:26]

        # Make sure values are positive and in MW
        df_consumption = df_consumption[df_consumption >= 0] / 1000

        hour = 0

        datapoints = list()

        for column in df_consumption.columns:

            datapoint_datetime = datetime.combine(co_datetime.date(), time(hour))

            datapoint = {
                "zoneKey": zone_key,
                "datetime": arrow.get(datapoint_datetime).replace(tzinfo=TZ).datetime,
                "consumption": df_consumption[column].values[0],
                "source": "xm.com.co",
            }

            datapoints.append(datapoint)

            hour += 1

        return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "CO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:

    # Convert datetime to local time
    if target_datetime:
        co_datetime = arrow.get(target_datetime).to(TZ)
    else:
        co_datetime = arrow.get(datetime.now() + timedelta(days=-3)).to(TZ)

    objetoAPI = pydataxm.ReadDB()

    # API request list of power plants with ID (column 1) and type (column 7)
    df_recursos = objetoAPI.request_data(
        "ListadoRecursos", "Sistema", co_datetime.date(), co_datetime.date()
    )

    # API request generation per power plant
    df_generation = objetoAPI.request_data(
        "Gene", "Recurso", co_datetime.date(), co_datetime.date()
    )

    if df_generation.empty:
        return []

    else:

        # Add column with XM type
        df_generation["XM Type"] = df_generation["Values_code"].apply(
            lambda x: df_recursos.loc[
                df_recursos["Values_Code"] == x, "Values_EnerSource"
            ].values[0]
        )

        # Add column with EMaps type from types dict
        df_generation["EM Type"] = df_generation["XM Type"].apply(
            lambda x: TYPES_XM_EM.get(x) if x in TYPES_XM_EM else "unknown"
        )

        # Get the generation values per hour and per EM type of production
        df_generation_type = df_generation.groupby(["EM Type"]).sum()

        # Make sure values are positive expressed in MW
        df_generation_type = df_generation_type[df_generation_type >= 0] / 1000

        hour = 0

        datapoints = list()

        for column in df_generation_type.columns:

            datapoint_datetime = datetime.combine(co_datetime.date(), time(hour))

            datapoint = {
                "zoneKey": zone_key,
                "datetime": arrow.get(datapoint_datetime).replace(tzinfo=TZ).datetime,
                "production": df_generation_type[column].to_dict(),
                "source": "xm.com.co",
            }

            datapoints.append(datapoint)

            hour += 1

        return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: str = "CO",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:

    # Convert datetime to local time
    if target_datetime:
        co_datetime = arrow.get(target_datetime).to(TZ)
    else:
        co_datetime = arrow.get(datetime.now() + timedelta(days=-3)).to(TZ)

    objetoAPI = pydataxm.ReadDB()

    # API request consumption
    df_price = objetoAPI.request_data(
        "PrecBolsNaci", "Sistema", co_datetime.date(), co_datetime.date()
    )
    if df_price.empty:
        return []

    else:

        # Get the price value for the requested hour in COP/MWh
        price_hour = df_price.iloc[:, co_datetime.hour].values[0] * 1000

        return {
            "zoneKey": zone_key,
            "datetime": arrow.get(co_datetime).replace(tzinfo=TZ).datetime,
            "currency": "COP",
            "price": price_hour,
            "source": "xm.com.co",
        }


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
