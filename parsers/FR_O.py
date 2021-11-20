#!/usr/bin/env python3
from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Dict

import arrow
from requests import Session

LIVE_ENDPOINTS = {
    "RE": "https://opendata-reunion.edf.fr/api/records/1.0/search/?dataset=prod-electricite-temps-reel&q=&lang=en&sort=date&timezone=Indian%2FReunion"
}

HISTORICAL_ENDPOINT = "https://opendata-corse-outremer.edf.fr/api/records/1.0/search/?dataset=courbe-de-charge-de-la-production-delectricite-par-filiere&q=&rows=24&sort=-date_heure&refine.date_heure={date}&refine.territoire={territoire}&timezone={tz}"
INSTALLED_CAP_ENPOINT = "https://opendata-corse-outremer.edf.fr/api/records/1.0/search/?dataset=registre-des-installations-de-production-et-de-stockage&rows=1000&q=&refine.codedepartement={dep}"

ZONEKEY_MAP = {
    "FR-COR": {
        "territoire": "Corse",
        "tz": "Europe/Paris",
        "departements": ["Haute-Corse", "Corse-du-Sud"],
    },
    "GF": {"territoire": "Guyane", "tz": "America/Cayenne"},
    "GP": {"territoire": "Guadeloupe", "tz": "America/Guadeloupe"},
    "MQ": {"territoire": "Martinique", "tz": "America/Martinique"},
    "RE": {"territoire": "Réunion", "tz": "Indian/Reunion"},
}


def get_none_negative(d: Dict[str, float], key: str) -> float:
    return max(d.get(key, 0), 0)


def fetch_production(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=None,
) -> List[dict]:
    session = session or Session()

    if not target_datetime:
        return get_live_data(zone_key, session)
    else:
        return get_historical_data(zone_key, session, target_datetime)


def get_historical_data(
    zone_key: str, session: Session, target_datetime: datetime
) -> List[dict]:
    formatted_date = target_datetime.strftime("%Y/%m/%d")
    zone_info = ZONEKEY_MAP[zone_key]
    endpoint = HISTORICAL_ENDPOINT.format(
        date=formatted_date, territoire=zone_info["territoire"], tz=zone_info["tz"]
    )

    hist_data = session.get(
        endpoint,
    ).json()
    datapoints = list()
    for record in hist_data["records"]:
        fields = record["fields"]
        datapoint = {
            "zoneKey": zone_key,
            "datetime": arrow.get(fields.get("date_heure")).datetime,
            "production": {
                "biomass": fields.get("bioenergies_mw"),
                "coal": fields.get("bagasse_charbon_mw"),
                "gas": 0,
                "hydro": fields.get("hydraulique_mw"),
                "nuclear": None,
                "oil": fields.get("thermique_mw"),
                "solar": get_none_negative(fields, "photovoltaique_mw"),
                "wind": get_none_negative(fields, "eolien_mw"),
                "geothermal": 0.0,
                "unknown": 0.0,
            },
            "source": endpoint.split("/")[2],
        }
        datapoints.append(datapoint)
    return datapoints


def get_live_data(zone_key: str, session: Session) -> List[dict]:
    endpoint = LIVE_ENDPOINTS.get(zone_key)
    if not endpoint:
        raise NotImplementedError(f"No live data available for {zone_key}")

    live_data = session.get(endpoint).json()

    datapoints = list()
    for record in live_data["records"]:
        fields = record["fields"]
        datapoint = {
            "zoneKey": zone_key,
            "datetime": arrow.get(fields.get("date")).datetime,
            "production": {
                "biomass": fields.get("bioenergies"),
                "coal": fields.get("charbon"),
                "gas": 0.0,
                "hydro": fields.get("hydraulique"),
                "nuclear": None,
                "oil": fields.get("diesel"),
                "solar": fields.get("photovoltaique"),
                "wind": fields.get("eolien"),
                "geothermal": 0.0,
                "unknown": 0.0,
            },
            "source": endpoint.split("/")[2],
        }
        datapoints.append(datapoint)
    return datapoints


def fetch_installed_capacity(
    zone_key: str, session: Optional[Session] = None
) -> Dict[str, float]:
    session = session or Session()

    departements = ZONEKEY_MAP[zone_key].get(
        "departements", [ZONEKEY_MAP[zone_key]["territoire"]]
    )

    installed_cap = defaultdict(lambda: 0)
    for departement in departements:
        endpoint = INSTALLED_CAP_ENPOINT.format(dep=departement)
        local_installed_cap = session.get(endpoint).json()
        for infra in local_installed_cap["records"]:
            fields = infra["fields"]
            installed_cap[fields["codefiliere"]] += fields["puismaxinstallee"] / 1000

    return installed_cap


def fetch_price(
    zone_key: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger=None,
) -> dict:
    # This data is not provided anymore by edf since 2019 !

    if target_datetime is None:
        raise NotImplementedError(f"No live price data available for {zone_key}")

    session = session or Session()
    formatted_date = target_datetime.strftime("%Y/%m/%d")
    zone_info = ZONEKEY_MAP[zone_key]
    endpoint = HISTORICAL_ENDPOINT.format(
        date=formatted_date, territoire=zone_info["territoire"], tz=zone_info["tz"]
    )

    hist_data = session.get(
        endpoint,
    ).json()

    if not hist_data["records"]:
        raise ValueError(f"No historical data found for {zone_key}")

    prices = list()
    for record in hist_data["records"]:
        price = record["fields"]["cout_moyen_de_production_eur_mwh"]
        if price:
            prices.append(price)

    mean_eur_price = sum(prices) / len(prices)

    return {
        "zoneKey": zone_key,
        "datetime": arrow.get(hist_data["records"][0]["fields"]["date_heure"]).datetime,
        "currency": "EUR",
        "price": mean_eur_price,
        "source": endpoint.split("/")[2],
    }
