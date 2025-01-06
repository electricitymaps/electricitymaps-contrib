#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pydataxm.pydataxm as pydataxm
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from parsers.lib.config import refetch_frequency, use_proxy
from parsers.lib.exceptions import ParserException

#   PARSER FOR COLOMBIA / DEMAND-ONLY as of 2023-02-11 / 5-minute-granularity / returns demand data of the recent day
#   MAIN_WEBSITE = https://www.xm.com.co/consumo/demanda-en-tiempo-real
CO_DEMAND_URL = "https://serviciosfacturacion.xm.com.co/XM.Portal.Indicadores/api/Operacion/DemandaTiempoReal"

ZONE_INFO = ZoneInfo("America/Bogota")  # UTC-5

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


# settle with fetching production and price data from past days, as data doesn't
# seem to be available for very recent days
XM_DELAY_MIN = 2
XM_DELAY_MAX = 5


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="CO", monkeypatch_for_pydataxm=True)
def fetch_consumption(
    zone_key: ZoneKey = ZoneKey("CO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        session = session or Session()
        return _fetch_live_consumption(zone_key, session, logger)
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)
        return _fetch_historical_consumption(zone_key, target_datetime, logger)


def _fetch_live_consumption(
    zone_key: ZoneKey,
    session: Session,
    logger: Logger,
) -> list[dict[str, Any]]:
    response: Response = session.get(CO_DEMAND_URL, verify=False)
    if not response.ok:
        raise ParserException(
            parser="CO",
            message=f"Error fetching data: {response.status_code} {response.reason}",
            zone_key=zone_key,
        )

    demand_data = response.json()["Variables"][0]["Datos"]
    demand_list = TotalConsumptionList(logger)
    for datapoint in demand_data:
        dt_string = datapoint["Fecha"]
        # TODO: Remove the truncation of sub-seconds when we run on Python 3.11
        #       or above and fromisoformat can parse such strings
        if dt_string.find(".") != -1:
            dt_string = dt_string[: dt_string.find(".")]
        dt = datetime.fromisoformat(dt_string).replace(tzinfo=ZONE_INFO)
        demand_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=round(datapoint["Valor"], 1),
            source="xm.com.co",
        )
    return demand_list.to_list()


def _fetch_historical_consumption(
    zone_key: ZoneKey,
    target_datetime: datetime,
    logger: Logger,
) -> list[dict[str, Any]]:
    # API request consumption
    objetoAPI = pydataxm.ReadDB()
    df_consumption = objetoAPI.request_data(
        "DemaReal",
        "Sistema",
        target_datetime.date(),
        target_datetime.date(),
    )
    if df_consumption.empty:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime} : no consumption data available",
            zone_key=zone_key,
        )

    demand_list = TotalConsumptionList(logger)
    hour_columns = [col for col in df_consumption.columns if "Hour" in col]
    for col in hour_columns:
        consumption = float(df_consumption[col]) / 1000
        dt = target_datetime.replace(hour=int(col[-2:]) - 1)
        demand_list.append(
            zoneKey=zone_key,
            datetime=dt,
            consumption=consumption,
            source="xm.com.co",
        )
    return demand_list.to_list()


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="CO", monkeypatch_for_pydataxm=True)
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
        target_date_range = [
            target_datetime.date() - timedelta(days=days)
            for days in range(XM_DELAY_MIN, XM_DELAY_MAX + 1)
        ]
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)
        target_date_range = [target_datetime.date()]

    acquired_datetime = None
    objetoAPI = pydataxm.ReadDB()
    for date in target_date_range:
        # API request list of power plants with ID (column 1) and type (column 7)
        df_recursos = objetoAPI.request_data("ListadoRecursos", "Sistema", date, date)
        # API request generation per power plant
        df_generation = objetoAPI.request_data("Gene", "Recurso", date, date)
        if not df_generation.empty and not df_recursos.empty:
            acquired_datetime = datetime.combine(date, datetime.min.time()).replace(
                tzinfo=ZONE_INFO
            )
            break
    if not acquired_datetime:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime}: no production data available",
            zone_key=zone_key,
        )

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

        dt = acquired_datetime.replace(hour=int(col[-2:]) - 1)
        production_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production_mix,
            source="xm.com.co",
        )
    return production_list.to_list()


@refetch_frequency(timedelta(days=1))
@use_proxy(country_code="CO", monkeypatch_for_pydataxm=True)
def fetch_price(
    zone_key: ZoneKey = ZoneKey("CO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    if target_datetime is None:
        target_datetime = datetime.now(ZONE_INFO)
        target_date_range = [
            target_datetime.date() - timedelta(days=days)
            for days in range(XM_DELAY_MIN, XM_DELAY_MAX + 1)
        ]
    else:
        target_datetime = target_datetime.astimezone(ZONE_INFO)
        target_date_range = [target_datetime.date()]

    acquired_datetime = None
    objetoAPI = pydataxm.ReadDB()
    for date in target_date_range:
        df_price = objetoAPI.request_data("PrecBolsNaci", "Sistema", date, date)
        if not df_price.empty:
            acquired_datetime = datetime.combine(date, datetime.min.time()).replace(
                tzinfo=ZONE_INFO
            )
            break
    if not acquired_datetime:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime}: no price data available",
            zone_key=zone_key,
        )

    price_list = PriceList(logger)
    hour_columns = [col for col in df_price.columns if "Hour" in col]
    for col in hour_columns:
        price = float(df_price[col])
        dt = acquired_datetime.replace(hour=int(col[-2:]) - 1)
        price_list.append(
            zoneKey=zone_key,
            datetime=dt,
            currency="COP",
            price=price,
            source="xm.com.co",
        )
    return price_list.to_list()


if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_price() ->")
    print(fetch_price())
