from datetime import datetime, timedelta
from logging import getLogger
from typing import Any

import numpy as np
import pandas as pd
from requests import Session

from electricitymap.contrib.config import ZoneKey

logger = getLogger(__name__)
MODE_MAPPING = {
    "Wind Onshore": "wind",
    "Wind Offshore": "wind",
    "Solar": "solar",
    "Other renewable": "unknown",
    "Other": "unknown",
    "Nuclear": "nuclear",
    "Hydro Run-of-river and poundage": "hydro",
    "Fossil Hard coal": "coal",
    "Fossil Gas": "gas",
    "Biomass": "biomass",
    "Hydro Pumped Storage": "hydro storage",
}

SOURCE = "bmreports.com"
BMREPORTS_base_url = "https://data.elexon.co.uk/bmrs/api/v1/datasets/IGCA"


def fetch_production_capacity(
    zone_key: ZoneKey, target_datetime: datetime, session: Session
) -> dict[str, Any] | None:
    start_date = (target_datetime - timedelta(days=366)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = target_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"{BMREPORTS_base_url}?publishDateTimeFrom={start_date}&publishDateTimeTo={end_date}&format=json"

    r = session.get(url)
    if r.status_code != 200:
        raise ValueError(
            f"GB: No capacity data available for year {target_datetime.year}. {r.status_code} :{r.text}"
        )
    else:
        if r.json()["data"] == []:
            raise ValueError(
                f"GB: No capacity data available for year {target_datetime.year}. {r.status_code} :{r.text}"
            )
        df = pd.DataFrame(r.json()["data"])
        df["datetime"] = pd.to_datetime(df["year"].astype(str) + "-01-01").dt.strftime(
            "%Y-%m-%d"
        )
        df["mode"] = df["psrType"].str.strip().map(MODE_MAPPING)
        df["source"] = SOURCE
        df["value"] = pd.to_numeric(np.round(df["quantity"], 0), downcast="integer")
        df_result = (
            df[["datetime", "value", "mode", "source"]]
            .groupby(["datetime", "mode", "source"])
            .sum(numeric_only=True)
            .reset_index()
        )
        result = {}
        for _, row in df_result.iterrows():
            result[row["mode"]] = {
                "datetime": row["datetime"],
                "value": row["value"],
                "source": row["source"],
            }
        logger.info(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{df}"
        )

        return result


if __name__ == "__main__":
    print(fetch_production_capacity("GB", datetime(2024, 1, 1), Session()))
