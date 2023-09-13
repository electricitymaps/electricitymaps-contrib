#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any

import arrow
import pydataxm.pydataxm as pydataxm
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

#   PARSER FOR COLOMBIA / DEMAND-ONLY as of 2023-02-11 / 5-minute-granularity / returns demand data of the recent day
#   MAIN_WEBSITE = https://www.xm.com.co/consumo/demanda-en-tiempo-real
colombia_demand_URL = "https://serviciosfacturacion.xm.com.co/XM.Portal.Indicadores/api/Operacion/DemandaTiempoReal"

TZ = "America/Bogota"  # UTC-5

# dictionnary of plant types XM to EMaps https://www.xm.com.co/generacion/tipos
PRODUCTION_MAPPING = {
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

XM_DELAY_MIN = 2
XM_DELAY_MAX = 5


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = session or Session()

    if target_datetime is None:
        return fetch_live_consumption(zone_key, session, logger)
    else:
        return fetch_historical_consumption(zone_key, session, target_datetime, logger)


def fetch_live_consumption(
    zone_key: ZoneKey, session: Session, logger: Logger
) -> list[dict[str, Any]]:
    response: Response = session.get(colombia_demand_URL, verify=False)

    if not response.ok:
        raise ParserException(
            parser="CO",
            message=f"Error fetching data: {response.status_code} {response.reason}",
            zone_key=zone_key,
        )

    demand_json = response.json()
    demand_data = demand_json["Variables"][0]["Datos"]

    demand_list = TotalConsumptionList(logger)

    for datapoint in demand_data:
        demand_list.append(
            zoneKey=zone_key,
            datetime=arrow.get(datapoint["Fecha"], tzinfo=TZ).datetime,
            consumption=round(datapoint["Valor"], 1),
            source="xm.com.co",
        )
    return demand_list.to_list()


def fetch_historical_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    demand_list = TotalConsumptionList(logger)
    # Convert datetime to local time
    target_arrow_in_tz = arrow.get(target_datetime).to(TZ)

    objetoAPI = pydataxm.ReadDB()

    # API request consumption
    df_consumption = objetoAPI.request_data(
        "DemaReal", "Sistema", target_arrow_in_tz.date(), target_arrow_in_tz.date()
    )

    if not df_consumption.empty:
        hour_columns = [col for col in df_consumption.columns if "Hour" in col]
        for hour_col in hour_columns:
            target_datetime_in_tz = target_arrow_in_tz.datetime.replace(
                hour=int(hour_col[-2:]) - 1
            )
            consumption = float(df_consumption[hour_col]) / 1000
            demand_list.append(
                zoneKey=zone_key,
                datetime=target_datetime_in_tz,
                consumption=consumption,
                source="xm.com.co",
            )
        return demand_list.to_list()
    else:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime} : no consumption data available",
            zone_key=zone_key,
        )


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    objetoAPI = pydataxm.ReadDB()

    df_recursos = None
    df_generation = None
    target_arrow_in_tz = arrow.now()

    if target_datetime is None:
        target_arrow_in_tz = arrow.now().floor("day").to(TZ).shift(days=-XM_DELAY_MIN)
        # Allow retries for most recent data
        for xm_delay in range(XM_DELAY_MIN, XM_DELAY_MAX + 1):
            target_arrow_in_tz = arrow.now().floor("day").to(TZ).shift(days=-xm_delay)

            # API request list of power plants with ID (column 1) and type (column 7)
            df_recursos = objetoAPI.request_data(
                "ListadoRecursos",
                "Sistema",
                target_arrow_in_tz.date(),
                target_arrow_in_tz.date(),
            )
            df_generation = objetoAPI.request_data(
                "Gene", "Recurso", target_arrow_in_tz.date(), target_arrow_in_tz.date()
            )

            if not df_generation.empty and not df_recursos.empty:
                break
    else:
        target_arrow_in_tz = arrow.get(target_datetime).to(TZ)

        # API request list of power plants with ID (column 1) and type (column 7)
        df_recursos = objetoAPI.request_data(
            "ListadoRecursos",
            "Sistema",
            target_arrow_in_tz.date(),
            target_arrow_in_tz.date(),
        )

        # API request generation per power plant
        df_generation = objetoAPI.request_data(
            "Gene", "Recurso", target_arrow_in_tz.date(), target_arrow_in_tz.date()
        )

    if (
        df_generation is not None
        and not df_generation.empty
        and df_recursos is not None
        and not df_recursos.empty
    ):
        df_units = (
            df_recursos[["Values_Code", "Values_EnerSource"]]
            .copy()
            .set_index("Values_Code")
        )
        df_generation = df_generation.set_index("Values_code")
        df_generation_mapped = df_generation.join(df_units, how="left").reset_index()
        df_generation_mapped["Values_EnerSource"] = df_generation_mapped[
            "Values_EnerSource"
        ].map(PRODUCTION_MAPPING)

        filtered_columns = [
            col
            for col in df_generation_mapped.columns
            if "Hour" in col or "Values_EnerSource" in col
        ]
        df_generation_aggregated = (
            df_generation_mapped[filtered_columns].groupby("Values_EnerSource").sum()
        )

        production_list = ProductionBreakdownList(logger)
        for col in df_generation_aggregated.columns:
            production_kw = df_generation_aggregated[col].to_dict()
            # convert to MW
            production_mw = {
                mode: round(production_kw[mode] / 1000, 3) for mode in production_kw
            }
            # convert to ProductionMix
            production_mix = ProductionMix()

            for mode, value in production_mw.items():
                production_mix.add_value(mode, value)

            co_datetime = target_arrow_in_tz.datetime.replace(hour=int(col[-2:]) - 1)
            production_list.append(
                zoneKey=zone_key,
                datetime=co_datetime,
                production=production_mix,
                source="xm.com.co",
            )

        return production_list.to_list()
    else:
        raise ParserException(
            parser="CO",
            message=f"{target_arrow_in_tz.datetime}: no production data available",
            zone_key=zone_key,
        )


@refetch_frequency(timedelta(days=1))
def fetch_price(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    session = session or Session()

    objetoAPI = pydataxm.ReadDB()

    df_price = None
    target_arrow_in_tz = arrow.now()

    if target_datetime is None:
        # Allow retries for most recent data
        for xm_delay in range(XM_DELAY_MIN, XM_DELAY_MAX + 1):
            target_arrow_in_tz = arrow.now().floor("day").to(TZ).shift(days=-xm_delay)

            df_price = objetoAPI.request_data(
                "PrecBolsNaci",
                "Sistema",
                target_arrow_in_tz.date(),
                target_arrow_in_tz.date(),
            )

            if not df_price.empty:
                break
    else:
        target_arrow_in_tz = arrow.get(target_datetime).to(TZ)
        # API request consumption
        df_price = objetoAPI.request_data(
            "PrecBolsNaci",
            "Sistema",
            target_arrow_in_tz.date(),
            target_arrow_in_tz.date(),
        )

    price_list = PriceList(logger)
    if df_price is not None and not df_price.empty:
        hour_columns = [col for col in df_price.columns if "Hour" in col]
        for col in hour_columns:
            target_datetime_in_tz = target_arrow_in_tz.datetime.replace(
                hour=int(col[-2:]) - 1
            )
            price = float(df_price[col])

            price_list.append(
                zoneKey=zone_key,
                datetime=target_datetime_in_tz,
                currency="COP",
                price=price,
                source="xm.com.co",
            )
        return price_list.to_list()
    else:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime}: no price data available",
            zone_key=zone_key,
        )


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption(ZoneKey("CO")))

    print("fetch_live_production() ->")
    print(fetch_production(ZoneKey("CO")))

    print("fetch_production() ->")
    print(fetch_production(ZoneKey("CO")))

    print("fetch_price() ->")
    print(fetch_price(ZoneKey("CO")))
