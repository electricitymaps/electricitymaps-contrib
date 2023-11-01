from datetime import datetime
from logging import getLogger

from requests import Response, Session

from electricitymap.contrib.config import ZoneKey

"""Disclaimer: Capacity for the Spanish isles is only available per archipelago. This parser should not be used for the Canary Islands and the Balearic Islands as we do not get the capacity per island."""

logger = getLogger(__name__)
MODE_MAPPING = {
    "Hidráulica": "hydro",
    "Turbinación bombeo": "hydro storage",
    "Nuclear": "nuclear",
    "Carbón": "coal",
    "Fuel + Gas": "gas",
    "Ciclo combinado": "gas",
    "Eólica": "wind",
    "Solar fotovoltaica": "solar",
    "Solar térmica": "solar",
    "Otras renovables": "unknown",
    "Cogeneración": "gas",
    "Residuos no renovables": "unknown",
    "Residuos renovables": "biomass",
    "Motores diésel": "oil",
    "Turbina de gas": "gas",
    "Turbina de vapor": "gas",
}

GEO_LIMIT_TO_GEO_IDS = {
    "peninsular": 8741,
    "canarias": 19,
    "baleares": 18,
    "ceuta": 12,
    "melilla": 8746,
}

ZONE_KEY_TO_GEO_LIMIT = {
    "ES": "peninsular",
    # "ES-IB-FO": "baleares",
    # "ES-IB-IZ": "baleares",
    # "ES-IB-MA": "baleares",
    # "ES-IB-ME": "baleares",
    # "ES-CN-FVLZ": "canarias",
    # "ES-CN-GC": "canarias",
    # "ES-CN-HI": "canarias",
    # "ES-CN-IG": "canarias",
    # "ES-CN-LP": "canarias",
    # "ES-CN-TE": "canarias",
    "ES-CE": "ceuta",
    "ES-ML": "melilla",
}


def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime):
    geo_limit = ZONE_KEY_TO_GEO_LIMIT[zone_key]
    geo_ids = GEO_LIMIT_TO_GEO_IDS[geo_limit]
    url = "https://apidatos.ree.es/es/datos/generacion/potencia-instalada"
    params = {
        "start_date": target_datetime.strftime("%Y-01-01T00:00"),
        "end_date": target_datetime.strftime("%Y-12-31T23:59"),
        "time_trunc": "year",
        "geo_trunc": "electric_system",
        "geo_limit": geo_limit,
        "geo_ids": geo_ids,
        "tecno_select": "all",
    }

    r: Response = Session().get(url, params=params)
    if r.status_code == 200:
        data = r.json()["included"]
        capacity = {}
        for item in data:
            value: float = round(item["attributes"]["total"], 0)
            if item["type"] in MODE_MAPPING:
                mode = MODE_MAPPING[item["type"]]
                if mode in capacity:
                    capacity[mode]["value"] += value
                else:
                    mode_capacity = {
                        "datetime": target_datetime.strftime("%Y-%m-%d"),
                        "value": value,
                        "source": "ree.es",
                    }
                    capacity[mode] = mode_capacity
        logger.info(
            f"Fetched capacity for {zone_key} on {target_datetime.date()}: \n{capacity}"
        )
        return capacity
    else:
        logger.warning(
            f"{zone_key}: No capacity data available for year {target_datetime.year}"
        )


def fetch_production_capacity_for_all_zones(
    target_datetime: datetime,
) -> dict:
    ree_capacity = {}
    for zone in ZONE_KEY_TO_GEO_LIMIT:
        zone_capacity = fetch_production_capacity(zone, target_datetime)
        ree_capacity[zone] = zone_capacity
    logger.info(f"Fetched capacity for REE zones on {target_datetime.date()}")
    return ree_capacity


if __name__ == "__main__":
    fetch_production_capacity("ES", datetime(2023, 1, 1))
