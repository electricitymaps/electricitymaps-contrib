#!/usr/bin/env python3
# coding=utf-8

import json
import logging

import arrow
import requests

# APIs
HISTORICAL_API_ENDPOINT = (
    "https://opendata-corse-outremer.edf.fr/api/records/1.0/search/"
)
REAL_TIME_APIS = {
    "FR-COR": "https://opendata-corse.edf.fr/api/records/1.0/search",
    "RE": "https://opendata-reunion.edf.fr/api/records/1.0/search/",
}
# Sources
HISTORICAL_SOURCE = "https://opendata-corse-outremer.edf.fr"
REAL_TIME_SOURCES = {"FR-COR": "opendata-corse.edf.fr", "RE": "opendata-reunion.edf.fr"}
# Managed zones
zone_key_mapping = {
    "FR-COR": "Corse",
    "GF": "Guyane",
    "GP": "Guadeloupe",
    "MQ": "Martinique",
    "RE": "Réunion",
}

# -------------- Parametrized properties functions -------------- #


def get_param(zone_key: None, target_datetime: None):
    if target_datetime is None:
        params = {
            "FR-COR": {
                "dataset": "production-delectricite-par-filiere-en-temps-reel",
                "timezone": "Europe/Paris",
                "sort": "date",
                "rows": "288",
            },
            "RE": {
                "dataset": "prod-electricite-temps-reel",
                "timezone": "Indian/Reunion",
                "sort": "date",
                "rows": 288,
            },
        }
        return params[zone_key]
    else:
        datetime = arrow.get(target_datetime, tz="Europe/Paris")
        formatted_from = datetime.shift(days=-1).format("DD/MM/YYYY")
        formatted_to = datetime.format("DD/MM/YYYY")
        return {
            "dataset": "courbe-de-charge-de-la-production-delectricite-par-filiere",
            "timezone": "Europe/Paris",
            "q": "date_heure >= {} AND date_heure <= {}".format(
                formatted_from, formatted_to
            ),
            "sort": "date_heure",
            "rows": 24,
            "facet": "territoire",
            "refine.territoire": zone_key_mapping[zone_key],
        }


def get_api(zone_key: None, target_datetime: None):
    if target_datetime is None:
        return REAL_TIME_APIS[zone_key]
    else:
        return HISTORICAL_API_ENDPOINT


def get_source(zone_key: None, target_datetime: None):
    if target_datetime is None:
        return REAL_TIME_SOURCES[zone_key]
    else:
        return HISTORICAL_SOURCE


def get_date_name(zone_key: None, target_datetime: None):
    if target_datetime is None:
        return "date"
    else:
        return "date_heure"


# -------------- Bagasse / Coal Repartitions -------------- #

# Depending on the month, this correspond more or less to bagasse or coal.
# This map is an clumsy approximation using harvesting period and annual
# percentage of biomass used. Here, we use  17.17% for this percentage
# (https://fr.wikipedia.org/wiki/Usine_de_Bois_Rouge &
# https://fr.wikipedia.org/wiki/Usine_du_Gol)
MAP_GENERATION_BAGASSE_COAL_REUNION = {
    1: {"coal": 1, "biomass": 0},
    2: {"coal": 1, "biomass": 0},
    3: {"coal": 1, "biomass": 0},
    4: {"coal": 1, "biomass": 0},
    5: {"coal": 1, "biomass": 0},
    6: {"coal": 1, "biomass": 0},
    7: {"coal": 0.77, "biomass": 0.23},
    8: {"coal": 0.6, "biomass": 0.4},
    9: {"coal": 0.6, "biomass": 0.4},
    10: {"coal": 0.6, "biomass": 0.4},
    11: {"coal": 0.6, "biomass": 0.4},
    12: {"coal": 0.77, "biomass": 0.23},
}
# Depending on the month, this correspond more or less to bagasse or coal.
# This map is an clumsy approximation using harvesting period and annual
# percentage of biomass used. Here, we use  20% for this percentage
# (https://fr.wikipedia.org/wiki/Syst%C3%A8me_%C3%A9lectrique_de_la_Guadeloupe &
# https://www.guadeloupe-energie.gp/wp-content/uploads/2011/07/2010-10-01_Biomasse_Etat-des-lieux.pdf p.35)
MAP_GENERATION_BAGASSE_COAL_GUADELOUPE = {
    1: {"coal": 1, "biomass": 0},
    2: {"coal": 1, "biomass": 0},
    3: {"coal": 0.6, "biomass": 0.4},
    4: {"coal": 0.3, "biomass": 0.7},
    5: {"coal": 0.3, "biomass": 0.7},
    6: {"coal": 0.6, "biomass": 0.4},
    7: {"coal": 0.8, "biomass": 0.2},
    8: {"coal": 1, "biomass": 0},
    9: {"coal": 1, "biomass": 0},
    10: {"coal": 1, "biomass": 0},
    11: {"coal": 1, "biomass": 0},
    12: {"coal": 1, "biomass": 0},
}

# -------------- Thermal Repartitions -------------- #
# These approximations are made from this document :
# https://opendata-corse-outremer.edf.fr/api/datasets/1.0/courbe-de-charge-de-la-production-delectricite-par-filiere/attachments/bilan_electrique_edf_sei_2017_pdf/

MAP_GENERATION_DIESEL_GAS_REUNION = {"gas": 0.1202, "oil": 0.8798}
# (RE) API update: - gas suppression
MAP_GENERATION_REUNION_OIL = {"oil": 1}
MAP_GENERATION_REUNION_COAL = {"coal": 1}

MAP_GENERATION_DIESEL_GAS_MARTINIQUE = {"gas": 0.1247, "oil": 0.8753}
MAP_GENERATION_DIESEL_GAS_GUADELOUPE = {"gas": 0.0126, "oil": 0.9874}
MAP_GENERATION_DIESEL_GAS_GUYANNE = {"gas": 0.2261, "oil": 0.7739}
MAP_GENERATION_DIESEL_GAS_CORSE = {"gas": 0.0196, "oil": 0.9804}


# Thermal sources by region
thermal_mapping = {
    "FR-COR": [
        {
            "name": "thermique_mwh",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_CORSE,
        }
    ],
    "GF": [
        {
            "name": "thermique_mwh",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_GUYANNE,
        }
    ],
    "GP": [
        {
            "name": "bagasse_charbon_mwh",
            "monthly_variation": True,
            "type": MAP_GENERATION_BAGASSE_COAL_GUADELOUPE,
        },
        {
            "name": "thermique_mwh",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_GUADELOUPE,
        },
    ],
    "MQ": [
        {
            "name": "thermique_mwh",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_MARTINIQUE,
        }
    ],
    "RE": [
        {
            "name": "bagasse_charbon_mwh",
            "monthly_variation": True,
            "type": MAP_GENERATION_BAGASSE_COAL_REUNION,
        },
        {
            "name": "bagasse_charbon",
            "monthly_variation": True,
            "type": MAP_GENERATION_BAGASSE_COAL_REUNION,
        },
        {
            "name": "thermique_mwh",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_REUNION,
        },
        {
            "name": "thermique",
            "monthly_variation": False,
            "type": MAP_GENERATION_DIESEL_GAS_REUNION,
        },
        # (RE) API update
        {
            "name": "turbine_a_combustion",
            "monthly_variation": False,
            "type": MAP_GENERATION_REUNION_OIL,
        },
        {
            "name": "diesel",
            "monthly_variation": False,
            "type": MAP_GENERATION_REUNION_OIL,
        },
        {
            "name": "charbon",
            "monthly_variation": False,
            "type": MAP_GENERATION_REUNION_COAL,
        },
    ],
}

# Non-thermal sources names in api
sources_mapping = {
    "biomass": ["bioenergies_mwh", "bioenergies", "biogaz"],
    "hydro": ["hydraulique_mwh", "hydraulique", "micro_hydro"],
    "solar": [
        "photovoltaique_mwh",
        "photovoltaique",
        "photovoltaique_avec_stockage",
        "photovoltaique0",
    ],
    "wind": ["eolien_mwh", "eolien"],
    "geothermal": ["geothermie_mwh"],
    "oil": ["moteur_diesel"],
}


def fetch_production(
    zone_key=None,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if (target_datetime is None) and zone_key not in REAL_TIME_SOURCES.keys():
        raise NotImplementedError("There is no real time data")

    # Request build
    r = session or requests.session()
    params = get_param(zone_key, target_datetime)
    api = get_api(zone_key, target_datetime)
    date_name = get_date_name(zone_key, target_datetime)

    # Date build
    if target_datetime is None:
        datetime = arrow.now(tz=params["timezone"])
    else:
        datetime = arrow.get(target_datetime, params["timezone"])

    # Data retrievement
    response = r.get(api, params=params)
    data = json.loads(response.content)
    datapoints = []

    # Response build
    if len(data["records"]) > 0 and ("fields" in data["records"][0]):
        for i in range(0, len(data["records"])):
            fields = data["records"][i]["fields"]
            datetime_result = arrow.get(fields[date_name]).datetime
            result = {
                "zoneKey": zone_key,
                "datetime": datetime_result,
                "source": get_source(zone_key, target_datetime),
                "production": {
                    "nuclear": 0,
                    "biomass": 0,
                    "coal": 0,
                    "gas": 0,
                    "hydro": 0,
                    "oil": 0,
                    "solar": 0,
                    "wind": 0,
                    "geothermal": 0,
                    "unknown": 0,
                },
            }
            # Non-thermal sources
            for source_mapping_key in sources_mapping:
                current_sources = sources_mapping[source_mapping_key]
                for current_source in current_sources:
                    if current_source in fields:
                        value = fields[current_source]
                        if value > 0:
                            result["production"][source_mapping_key] += value

            # Thermal sources
            for k in range(0, len(thermal_mapping[zone_key])):
                current_thermal = thermal_mapping[zone_key][k]
                current_type = current_thermal["type"]
                current_source = None
                if current_thermal["monthly_variation"]:
                    current_source = current_type[datetime.month]
                else:
                    current_source = current_type
                for type_name in current_source:
                    if current_thermal["name"] in fields:
                        value = fields[current_thermal["name"]]
                        multiple = current_source[type_name]
                        result["production"][type_name] += value * multiple

            datapoints.append(result)

    return datapoints


def fetch_price(
    zone_key=None,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    if target_datetime is None:
        raise NotImplementedError("There is no real time data")

    r = session or requests.session()
    params = get_param(zone_key, target_datetime)
    api = get_api(zone_key, target_datetime)
    date_name = get_date_name(zone_key, target_datetime)

    r = session or requests.session()

    # Data retrievement
    response = r.get(api, params=params)
    data = json.loads(response.content)
    datapoints = []

    if len(data["records"]) > 0 and ("fields" in data["records"][0]):
        for i in range(0, len(data["records"])):
            fields = data["records"][i]["fields"]
            if "cout_moyen_de_production_eu_mwh" in fields:
                datetime_result = arrow.get(fields[date_name]).datetime
                datapoints.append(
                    {
                        "zoneKey": zone_key,
                        "currency": "EUR",
                        "datetime": datetime_result,
                        "source": get_source(zone_key, target_datetime),
                        "price": float(fields["cout_moyen_de_production_eu_mwh"]),
                    }
                )

    return datapoints
