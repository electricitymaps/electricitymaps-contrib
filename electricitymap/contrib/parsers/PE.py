#!/usr/bin/env python3
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency

logger = getLogger(__name__)

API_ENDPOINT = "https://www.coes.org.pe/Portal/portalinformacion/generacion"

TIMEZONE = ZoneInfo("America/Lima")

MAP_GENERATION = {
    "DIESEL": "oil",
    "RESIDUAL": "biomass",
    "CARBÓN": "coal",
    "GAS": "gas",
    "HÍDRICO": "hydro",
    "BIOGÁS": "biomass",
    "BAGAZO": "biomass",
    "SOLAR": "solar",
    "EÓLICA": "wind",
}
SOURCE = "coes.org.pe"


def parse_datetime(dt: str):
    return datetime.strptime(dt, "%Y/%m/%d %H:%M:%S").replace(
        tzinfo=TIMEZONE
    ) - timedelta(minutes=30)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("PE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)
    r = session or Session()

    # To guarantee a full 24 hours of data we must make 2 requests.
    response_url: Response = r.post(
        API_ENDPOINT,
        data={
            "fechaInicial": (target_datetime).strftime("%d/%m/%Y"),
            "fechaFinal": (target_datetime + timedelta(days=1)).strftime("%d/%m/%Y"),
            "indicador": 0,
        },
    )
    # Data in MW (it is production not generation) + local time, be careful.

    production_data = response_url.json()["GraficoTipoCombustible"]["Series"]

    # Transform production_data into a pandas DataFrame
    # First, collect all datetime values and validate consistency across all sources
    datetime_values = []
    if production_data and production_data[0]["Data"]:
        datetime_values = [data["Nombre"] for data in production_data[0]["Data"]]

    # Validate that all energy sources have the same datetime values
    for item in production_data:
        source_datetimes = [data["Nombre"] for data in item["Data"]]
        if source_datetimes != datetime_values:
            raise ValueError(
                f"Datetime values are not consistent across all sources: {source_datetimes} != {datetime_values}"
            )

    # Create DataFrame with datetime as index and energy sources as columns
    df_data = {"datetime": datetime_values}

    for item in production_data:
        source_name = item["Name"]
        values = [data["Valor"] for data in item["Data"]]
        df_data[source_name] = values

    # Convert to pandas DataFrame
    df = pd.DataFrame(df_data)

    # Parse datetime column with Peru timezone and set as index
    df["datetime"] = pd.to_datetime(df["datetime"], format="%Y/%m/%d %H:%M:%S")
    df["datetime"] = df["datetime"].dt.tz_localize(TIMEZONE)
    df = df.set_index("datetime")
    # Create production breakdown list
    production_breakdown_list = ProductionBreakdownList(logger)

    for datetime_idx, row in df.iterrows():
        productionMix = ProductionMix()

        # Add each energy source to the production mix
        for energy_source, value in row.items():
            if energy_source in MAP_GENERATION:
                production_mode = MAP_GENERATION[energy_source]
                productionMix.add_value(production_mode, round(float(value), 3))
            else:
                raise ValueError(f"Unknown energy source: {energy_source}")

        # Add production breakdown to the list
        # Convert pandas Timestamp to native datetime object
        native_datetime = datetime_idx.to_pydatetime()
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=native_datetime,
            source=SOURCE,
            production=productionMix,
        )

    return production_breakdown_list.to_list()


if __name__ == "__main__":
    fetch_production()
