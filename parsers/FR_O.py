from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from requests import Response, Session

DOMAIN_MAPPING = {
    "FR-COR": "https://opendata-corse.edf.fr",
    "RE": "https://opendata-reunion.edf.fr",
    "GF": "https://opendata-guyane.edf.fr",
    "MQ": "https://opendata-martinique.edf.fr",
    "GP": "https://opendata-guadeloupe.edf.fr",
}

LIVE_DATASETS = {
    "FR-COR": "production-delectricite-par-filiere-en-temps-reel",
    "GP": "mix-temps-reel-guadeloupe",
}

HISTORICAL_DATASETS = {
    "FR-COR": "production-delectricite-par-filiere",
    "RE": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "GF": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "MQ": "courbe-de-charge-de-la-production-delectricite-par-filiere",
    "GP": "courbe-de-charge-de-la-production-delectricite-par-filiere",
}

API_PARAMETER_GROUPS = {
    "production": {
        "biomass": [
            "biomasse",
            "biomasse_mw",
            "biomasse_mwh",
            "bioenergies",
            "bioenergies_mw",
            "bioenergies_mwh",
        ],
        "coal": [
            "charbon",
        ],
        "geothermal": [
            "geothermie",
            "geothermie_mw",
        ],
        "hydro": [
            "hydraulique",
            "hydraulique_mw",
            "hydraulique_mwh",
            "micro_hydro",
            "micro_hydraulique_mw",
        ],
        "oil": ["diesel", "moteur_diesel"],
        "solar": [
            "photovoltaique",
            "photovoltaique0",
            "photovoltaique_mw",
            "photovoltaique_mwh",
            "solaire_mw",
        ],
        "wind": [
            "eolien",
            "eolien_mw",
            "eolien_mwh",
        ],
        "unknown": [
            "bagasse_charbon_mwh",
            "charbon_bagasse_mw",
            "thermique_mw",
            "thermique_mwh",
            "turbines_a_combustion",
        ],
    },
    "storage": {},
}

PRODUCTION_MAPPING = {
    API_TYPE: type
    for key in ["production"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}

STORAGE_MAPPING = {
    API_TYPE: type
    for key in ["storage"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}


def generate_url(zone_key, target_datetime):
    return f"{DOMAIN_MAPPING[zone_key]}/api/v2/catalog/datasets/{HISTORICAL_DATASETS[zone_key] if target_datetime else LIVE_DATASETS[zone_key]}/exports/json"


def fetch_data(
    zone_key="", session=None, target_datetime=None, logger=None
) -> Tuple[Any, str]:
    ses = session or Session()
    target_datetime_string = None

    DATE_STRING_MAPPING = {
        "FR-COR": "date_heure" if target_datetime else "date",
        "RE": "date_heure",
        "GF": "date",
        "MQ": "date_heure",
        "GP": "date",
    }

    if target_datetime and zone_key not in HISTORICAL_DATASETS.keys():
        raise NotImplementedError(
            f"Historical data not implemented for {zone_key} in this parser."
        )
    elif target_datetime is None and zone_key not in LIVE_DATASETS.keys():
        raise NotImplementedError(
            f"Live data not implemented for {zone_key} in this parser."
        )

    URL_QUERIES: Dict[str, Union[str, None]] = {
        #   "refine": "statut:Validé" if target_datetime else None,
        "timezone": "UTC",
        "order_by": f"{DATE_STRING_MAPPING[zone_key]} desc",
        "refine": f"{DATE_STRING_MAPPING[zone_key]}:{target_datetime.strftime('%Y')}"
        if target_datetime
        else None,
    }

    url = generate_url(zone_key, target_datetime)
    response: Response = ses.get(url, params=URL_QUERIES)
    data = response.json()
    return data, DATE_STRING_MAPPING[zone_key]


def fetch_production(
    zone_key="FR-COR", session=None, target_datetime=None, logger=None
):
    data, date_string = fetch_data(zone_key, session, target_datetime, logger)
    return_list: List[Dict[str, Any]] = []
    for object in data:
        production: Dict[str, Union[float, int]] = {}
        storage: Dict[str, Union[float, int]] = {}
        for key in object:
            if key in PRODUCTION_MAPPING:
                if PRODUCTION_MAPPING[key] in production.keys():
                    production[PRODUCTION_MAPPING[key]] += object[key]
                else:
                    production[PRODUCTION_MAPPING[key]] = object[key]
                # Set values below 0 to 0
                production[PRODUCTION_MAPPING[key]] = (
                    production[PRODUCTION_MAPPING[key]]
                    if production[PRODUCTION_MAPPING[key]] >= 0
                    else 0
                )
            elif key in STORAGE_MAPPING:
                if STORAGE_MAPPING[key] in storage.keys():
                    storage[STORAGE_MAPPING[key]] += object[key]
                else:
                    storage[STORAGE_MAPPING[key]] = object[key]
        return_list.append(
            {
                "zoneKey": zone_key,
                "datetime": datetime.fromisoformat(object[f"{date_string}"]),
                "production": production,
                "storage": storage,
                "source": "edf.fr",
                "estimated": True if object["statut"] == "Estimé" else False,
            }
        )
    return return_list
