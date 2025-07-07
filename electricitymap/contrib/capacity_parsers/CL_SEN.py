import logging
from datetime import datetime
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

logger = logging.getLogger(__name__)

# Mapping conventional thermal as unknown as the production parser data is aggregated
MODE_MAPPING = {
    "Hídrico": "hydro",
    "Carbón": "unknown",
    "Diésel": "unknown",
    "Gas Natural": "unknown",
    "Eólico": "wind",
    "Solar": "solar",
    "Termosolar": "solar",
    "Geotérmico": "geothermal",
    "Otros*": "unknown",
}

SOURCE = "coordinador.cl"


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    url = "https://www.coordinador.cl/reportes-y-estadisticas/#Estadisticas"
    r: Response = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    capacity_link = soup.find_all(
        "a", href=lambda x: x and "hist_cap_inst_por_tecnologia" in x
    )
    if not len(capacity_link):
        logger.error(
            f"{zone_key}: No capacity data available for year {target_datetime.year}"
        )

    df = pd.read_excel(
        capacity_link[0].get("href"),
        sheet_name="Capacidad por Tecnología",
        header=2,
        skipfooter=2,
    )
    df = df.drop(columns=["Unnamed: 0", "TOTAL"])
    df = df.rename(columns={"Año": "datetime"})
    df = df.melt(id_vars=["datetime"], var_name="mode", value_name="value")
    df["mode"] = df["mode"].apply(lambda x: MODE_MAPPING[x.strip()])

    df = df.groupby(["datetime", "mode"])[["value"]].sum().reset_index()

    if target_datetime.year in df["datetime"].unique():
        df = df.loc[df["datetime"] == target_datetime.year]
        capacity = {}
        for _idx, data in df.iterrows():
            mode_capacity = {}
            mode_capacity["datetime"] = target_datetime.strftime("%Y-%m-%d")
            mode_capacity["value"] = round(data["value"], 0)
            mode_capacity["source"] = SOURCE
            capacity[data["mode"]] = mode_capacity
        logger.info(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n {capacity}"
        )
        return capacity
    else:
        logger.error(
            f"{zone_key}: No capacity data available for year {target_datetime.year}"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    fetch_production_capacity("CL-SEN", datetime(2022, 1, 1), Session())
