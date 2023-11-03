from datetime import datetime
from logging import getLogger
from typing import Dict, Union

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

"""Disclaimer: this parser does not include distributed capacity.
Solar capacity is much lower than in reality because the majority is distributed.
This capacity is not available in this dataset and should collected from the link below and added manually to the zone configuration.
Distributed solar generation is available here (tipo de usina = Geracao Distribuida): https://www.ons.org.br/Paginas/resultados-da-operacao/historico-da-operacao/capacidade_instalada.aspx"""
logger = getLogger(__name__)
CAPACITY_URL = "https://ons-dl-prod-opendata.s3.amazonaws.com/dataset/capacidade-geracao/CAPACIDADE_GERACAO.csv"
MODE_MAPPING = {
    "HIDRÁULICA": "hydro",
    "ÓLEO DIESEL": "unknown",
    "ÓLEO COMBUSTÍVEL": "unknown",
    "MULTI-COMBUSTÍVEL GÁS/DIESEL": "unknown",
    "MULTI-COMBUSTÍVEL DIESEL/ÓLEO": "unknown",
    "GÁS": "unknown",
    "RESÍDUO CICLO COMBINADO": "unknown",
    "EÓLICA": "wind",
    "CARVÃO": "unknown",
    "BIOMASSA": "unknown",
    "NUCLEAR": "nuclear",
    "RESÍDUOS INDUSTRIAIS": "unknown",
    "FOTOVOLTAICA": "solar",
}

REGION_MAPPING = {
    "NORDESTE": "BR-NE",
    "NORTE": "BR-N",
    "SUDESTE": "BR-CS",
    "SUL": "BR-S",
}

SOURCE = "ons.org.br"


def filter_data_by_date(data: pd.DataFrame, target_datetime: datetime) -> pd.DataFrame:
    """Filter capacity data for all rows that have:
    - start <= target_datetime : the power plant was connected before the considered target_datetime
    - end >= target_datetime : the power plant was not closed before the considered target_datetime
    """
    df = data.copy()

    df = df[
        (df["start"] <= target_datetime)
        & ((df["end"] >= target_datetime) | (df["end"].isna()))
    ]

    return df


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime, session: Session | None = None
) -> Union[Dict, None]:
    session = session or Session()
    r: Response = session.get(CAPACITY_URL)
    df = pd.read_csv(r.url, sep=";")
    df = df[
        [
            "nom_subsistema",
            "nom_combustivel",
            "dat_entradaoperacao",
            "dat_desativacao",
            "val_potenciaefetiva",
        ]
    ]
    df = df.rename(
        columns={
            "nom_subsistema": "zone_key",
            "nom_combustivel": "mode",
            "dat_entradaoperacao": "start",
            "dat_desativacao": "end",
            "val_potenciaefetiva": "value",
        }
    )

    # convert start and end columns to datetime
    df["start"] = df["start"].apply(
        lambda x: pd.to_datetime(x, utc=False).replace(day=1, month=1)
    )
    df["end"] = df["end"].apply(
        lambda x: pd.to_datetime(x, utc=False).replace(day=31, month=12)
        if x is not None
        else x
    )
    df = filter_data_by_date(df, target_datetime)
    df["datetime"] = target_datetime
    df["mode"] = df["mode"].map(MODE_MAPPING)
    df["zone_key"] = df["zone_key"].map(REGION_MAPPING)

    df = df.groupby(["zone_key", "mode", "datetime"])[["value"]].sum().reset_index()
    if not df.empty:
        capacity = {}
        for zone in df["zone_key"].unique():
            zone_capacity_df = df.loc[df["zone_key"] == zone]
            zone_capacity = {}
            for idx, data in zone_capacity_df.iterrows():
                mode_capacity = {
                    "datetime": target_datetime.strftime("%Y-%m-%d"),
                    "value": round(data["value"], 0),
                    "source": SOURCE,
                }

                zone_capacity[data["mode"]] = mode_capacity
            capacity[zone] = zone_capacity
        return capacity
    else:
        logger.error(f"No capacity data for ONS in {target_datetime}")


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session | None = None
) -> dict:
    session = session or Session()
    capacity = fetch_production_capacity_for_all_zones(target_datetime, session)[
        zone_key
    ]
    logger.info(f"Fetched capacity for {zone_key} in {target_datetime}: \n{capacity}")
    return capacity


if __name__ == "__main__":
    print(fetch_production_capacity("BR-N", datetime(2021, 1, 1), Session()))
