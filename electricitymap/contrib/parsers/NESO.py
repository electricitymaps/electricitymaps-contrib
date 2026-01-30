from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.exceptions import ParserException

NESO_API = "https://api.neso.energy/api/3/action/datastore_search_sql"
NESO_GENERATION_DATASET_ID = "f93d1835-75bc-43e5-84ad-12472b180a98"

NESO_TO_PRODUCTION_MIX_MAPPING = {
    "BIOMASS": "biomass",
    "COAL": "coal",
    "GAS": "gas",
    "HYDRO": "hydro",
    "NUCLEAR": "nuclear",
    "SOLAR": "solar",
    "WIND": "wind",
    "WIND_EMB": "wind",
    "OTHER": "unknown",
}

NESO_TO_STORAGE_MIX_MAPPING = {
    "STORAGE": "hydro",  # Classify storage as hydro storage since ELEXON uses this mapping
}


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    session = session or Session()

    if target_datetime is None:
        start_datetime = datetime.now(tz=ZoneInfo("UTC")) - timedelta(hours=24)
        sql_query = f"""SELECT * FROM "{NESO_GENERATION_DATASET_ID}" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""

    elif target_datetime > datetime(year=2009, month=1, day=1):
        target_datetime = target_datetime.astimezone(ZoneInfo("Europe/London"))
        start_datetime = target_datetime - timedelta(hours=24)
        end_datetime = target_datetime + timedelta(hours=24)

        sql_query = f"""SELECT * FROM "{NESO_GENERATION_DATASET_ID}" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' AND "DATETIME" <= '{end_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""
    else:
        raise ParserException(
            "NESO.py",
            "This parser is not yet able to parse dates before 2009-01-01",
            zone_key,
        )

    params = {"sql": sql_query}

    res: Response = session.get(NESO_API, params=params)
    if not res.status_code == 200:
        raise ParserException(
            "NESO.py",
            f"Exception when fetching production error code: {res.status_code}: {res.text}",
            zone_key,
        )

    obj = res.json()["result"]["records"]

    for row in obj:
        production_list = ProductionBreakdownList(logger=logger)
        production_mix = ProductionMix()

        for neso_key, emaps_key in NESO_TO_PRODUCTION_MIX_MAPPING.items():
            production_mix.add_value(emaps_key, float(row[neso_key]))

        storage_mix = StorageMix()
        for neso_key, emaps_key in NESO_TO_STORAGE_MIX_MAPPING.items():
            storage_mix.add_value(
                emaps_key,
                float(row[neso_key]) * -1 if float(row[neso_key]) != 0 else 0,
            )

        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(row["DATETIME"]).replace(
                tzinfo=ZoneInfo("UTC")
            ),
            production=production_mix,
            storage=storage_mix,
            source="neso.energy",
        )

    return production_list.to_list()
