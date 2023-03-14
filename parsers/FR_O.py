from datetime import datetime
from logging import getLogger
from typing import Any, Dict, List, Optional, Tuple, Union

from requests import Response, Session

from .lib.exceptions import ParserException

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
        "gas": [
            "thermique_mw",
            "thermique_mwh",
            "turbines_a_combustion",
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
        "unknown": ["bagasse_charbon_mwh", "charbon_bagasse_mw"],
    },
    "storage": {"battery": ["solde_stockage"]},
    "price": {
        "price": ["cout_moyen_de_production_eur_mwh"],
    },
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

PRICE_MAPPING = {
    API_TYPE: type
    for key in ["price"]
    for type, groups in API_PARAMETER_GROUPS[key].items()
    for API_TYPE in groups
}


def generate_url(zone_key, target_datetime):
    return f"{DOMAIN_MAPPING[zone_key]}/api/v2/catalog/datasets/{HISTORICAL_DATASETS[zone_key] if target_datetime else LIVE_DATASETS[zone_key]}/exports/json"


def fetch_data(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger(__name__),
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
        raise ParserException(
            "FR_O.py",
            f"Historical data not implemented for {zone_key} in this parser.",
            zone_key,
        )
    elif target_datetime is None and zone_key not in LIVE_DATASETS.keys():
        raise ParserException(
            "FR_O.py",
            f"Live data not implemented for {zone_key} in this parser.",
            zone_key,
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
    if data == []:
        raise ParserException(
            "FR_O.py",
            f"No data available for {zone_key} for {target_datetime.strftime('%Y')}"
            if target_datetime
            else f"No live data available for {zone_key}.",
            zone_key,
        )
    elif isinstance(data, dict):
        if data.get("errorcode") == "10002":
            raise ParserException(
                "FR_O.py",
                f"Rate limit exceeded. Please try again later after: {data.reset_time}",
            )
        elif data.get("error_code") == "ODSQLError":
            raise ParserException(
                "FR_O.py",
                "Query malformed. Please check the parameters. If this was previously working there has likely been a change in the API.",
            )
    return data, DATE_STRING_MAPPING[zone_key]


def fetch_production(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger(__name__),
):
    production_objects, date_string = fetch_data(
        zone_key, session, target_datetime, logger
    )

    return_list: List[Dict[str, Any]] = []
    for production_object in production_objects:
        production: Dict[str, Union[float, int]] = {}
        storage: Dict[str, Union[float, int]] = {}
        for mode_key in production_object:
            if mode_key in PRODUCTION_MAPPING:
                if PRODUCTION_MAPPING[mode_key] in production.keys():
                    production[PRODUCTION_MAPPING[mode_key]] += production_object[
                        mode_key
                    ]
                else:
                    production[PRODUCTION_MAPPING[mode_key]] = production_object[
                        mode_key
                    ]
                # Set values below 0 to 0
                production[PRODUCTION_MAPPING[mode_key]] = (
                    production[PRODUCTION_MAPPING[mode_key]]
                    if production[PRODUCTION_MAPPING[mode_key]] >= 0
                    else 0
                )
            elif mode_key in STORAGE_MAPPING:
                if STORAGE_MAPPING[mode_key] in storage.keys():
                    storage[STORAGE_MAPPING[mode_key]] += (
                        production_object[mode_key] * -1
                    )
                else:
                    storage[STORAGE_MAPPING[mode_key]] = (
                        production_object[mode_key] * -1
                    )
        return_list.append(
            {
                "zoneKey": zone_key,
                "datetime": datetime.fromisoformat(production_object[f"{date_string}"]),
                "production": production,
                "storage": storage,
                "source": "edf.fr",
                # TODO: Should be re-enabled when the changes discussed in #4828 are implemented
                # "estimated": True if production_object["statut"] == "Estimé" else False,
            }
        )
    return return_list


def fetch_price(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=getLogger(__name__),
):
    data_objects, date_string = fetch_data(zone_key, session, target_datetime, logger)

    return_list: List[Dict[str, Any]] = []
    for data_object in data_objects:
        price: Union[float, int, None] = None
        for mode_key in data_object:
            if mode_key in PRICE_MAPPING:
                price = data_object[mode_key]
                break

        return_list.append(
            {
                "zoneKey": zone_key,
                "currency": "EUR",
                "datetime": datetime.fromisoformat(data_object[f"{date_string}"]),
                "source": "edf.fr",
                "price": price,
            }
        )
    return return_list
