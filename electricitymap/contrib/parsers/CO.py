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
from electricitymap.contrib.parsers.lib.config import refetch_frequency, use_proxy
from electricitymap.contrib.parsers.lib.exceptions import ParserException

# The production, price, and historical consumption parser makes use of a third
# party library called pydataxm, for details on what data is available, refer to
# https://github.com/EquipoAnaliticaXM/API_XM/?tab=readme-ov-file#variables-disponibles-para-consumir-en-la-api-xm.
#
# Note:
# - Currently there is a delay of two days for data to be made available via
#   this library.
# - Sometimes fetching data with start date / end date being the same day, you
#   can get a full month of days.
#
# Delay live production and price data fetches, as data isn't made available
# that quick when using the pydataxm library
XM_DELAY_MIN = 2
XM_DELAY_MAX = 5

# Fetching live consumption is done using another API currently, which as of
# 2023-02-11 provides demand data with 5-minute-granularity of the current day.
# For details, refer to https://www.xm.com.co/consumo/demanda-en-tiempo-real.
#
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
    response.raise_for_status()

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
    api_client = pydataxm.ReadDB()
    target_date = target_datetime.date()

    # get system demand
    df_cons = api_client.request_data("DemaReal", "Sistema", target_date, target_date)
    if df_cons.empty:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime} : no consumption data available",
            zone_key=zone_key,
        )

    # preserve the date column as the index
    df_cons = df_cons.set_index("Date")

    # filter out column of relevance: hour
    df_cons = df_cons[[c for c in df_cons.columns if "Hour" in c]]

    consumption_list = TotalConsumptionList(logger)
    for date, df in df_cons.groupby("Date"):
        for hour_col in df.columns:
            consumption = float(df[hour_col]) / 1000

            # hour_col is "Values_Hour01" to "Values_Hour24"
            hour = int(hour_col[-2:]) - 1
            dt = date.to_pydatetime().replace(hour=hour).replace(tzinfo=ZONE_INFO)

            consumption_list.append(
                zoneKey=zone_key,
                datetime=dt,
                consumption=consumption,
                source="xm.com.co",
            )
    return consumption_list.to_list()


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

    api_client = pydataxm.ReadDB()
    for date in target_date_range:
        # get power production resources, where we are interested in a mapping
        # between a resource id (Values_Code column) to power production type
        # (Values_EnerSource column)
        df_res = api_client.request_data("ListadoRecursos", "Sistema", date, date)
        if df_res.empty:
            continue

        # get power production per resource
        df_prod = api_client.request_data("Gene", "Recurso", date, date)
        if df_prod.empty:
            continue

        break
    if df_prod.empty:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime}: no production data available",
            zone_key=zone_key,
        )

    # join the Values_EnerSource column from df_res to df_prod using Values_code column
    df_res = df_res[["Values_Code", "Values_EnerSource"]].set_index("Values_Code")
    df_prod = df_prod.set_index("Values_code")
    df_prod = df_prod.join(df_res, how="left").reset_index()

    # map power production type values to our terminology
    df_prod["Values_EnerSource"] = df_prod["Values_EnerSource"].map(PRODUCTION_MAPPING)

    # filter out columns of relevance: date, hour, and power production type
    df_cols = [
        c
        for c in df_prod.columns
        if "Date" in c or "Hour" in c or "Values_EnerSource" in c
    ]
    df_prod = df_prod[df_cols]

    # sum all values for given combination of date and power production type,
    # and make a multi index of those combinations
    df_prod = df_prod.groupby(["Date", "Values_EnerSource"]).sum(
        numeric_only=True,
    )

    # loop over each date in the multi index
    production_list = ProductionBreakdownList(logger)
    for date, df in df_prod.groupby(level=0):
        # in the date specific df, drop the date from the index, leaving the
        # power production type as index
        df = df.droplevel(0)

        for hour_col in df.columns:
            prod_kw = df[hour_col].to_dict()
            prod_mw = {mode: round(kw / 1000, 3) for mode, kw in prod_kw.items()}

            production_mix = ProductionMix()
            for mode, value in prod_mw.items():
                production_mix.add_value(mode, value)

            # hour_col is "Values_Hour01" to "Values_Hour24"
            hour = int(hour_col[-2:]) - 1
            dt = date.to_pydatetime().replace(hour=hour).replace(tzinfo=ZONE_INFO)

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

    api_client = pydataxm.ReadDB()
    for date in target_date_range:
        df_price = api_client.request_data("PrecBolsNaci", "Sistema", date, date)
        if df_price.empty:
            continue
        break
    if df_price.empty:
        raise ParserException(
            parser="CO",
            message=f"{target_datetime}: no price data available",
            zone_key=zone_key,
        )

    # preserve the date column as the index
    df_price = df_price.set_index("Date")

    # filter out column of relevance: hour
    df_price = df_price[[c for c in df_price.columns if "Hour" in c]]

    price_list = PriceList(logger)
    for date, df in df_price.groupby("Date"):
        for hour_col in df.columns:
            price = float(df[hour_col])

            # hour_col is "Values_Hour01" to "Values_Hour24"
            hour = int(hour_col[-2:]) - 1
            dt = date.to_pydatetime().replace(hour=hour).replace(tzinfo=ZONE_INFO)

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

    dt = datetime.fromisoformat("2025-01-01T00:00:00-05:00")
    print("fetch_production(target_datetime=...) ->")
    print(fetch_production(target_datetime=dt))

    print("fetch_price(target_datetime=...) ->")
    print(fetch_price(target_datetime=dt))

    print("fetch_consumption(target_datetime=...) ->")
    print(fetch_consumption(target_datetime=dt))
