from datetime import timedelta, timezone
import logging

# The arrow library is used to handle datetimes
#import arrow

# The request library is used to fetch content through HTTP
import requests
# pandas processes tabular data
#import pandas as pd

from pprint import pprint
import json

PRODUCTION_URL = "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/production.json"
CONSUMPTION_URL = "https://www.hydroquebec.com/data/documents-donnees/donnees-ouvertes/json/demande.json"


def fetch_production(
    zone_key="CA-QC",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given region.
       In this particular case, translated mapping of JSON keys are also required"""

    def if_exists(elem: dict, etype: str):

        english = {
            "hydraulique": "hydro",
            "thermique": "thermal",
            "solaire": "solar",
            "eolien": "wind",
            "autres": "unknown",
            "valeurs": "values",
        }
        english = {v: k for k, v in english.items()}
        try:
            return elem["valeurs"][english[etype]]
        except KeyError:
            return 0.0

    data = _fetch_quebec_production()
    for elem in reversed(data["details"]):
        if elem["valeurs"]["total"] != 0:

            return {
                "zoneKey": zone_key,
                "datetime": elem["date"],
                "production": {
                    "biomass": 0.0,
                    "coal": 0.0,
                    "gas": 0.0,
                    "hydro": if_exists(elem, "hydro"),
                    "nuclear": 0.0,
                    "oil": 0.0,
                    "solar": if_exists(elem, "solar"),
                    "wind": if_exists(elem, "wind"),
                    "geothermal": if_exists(elem, "geothermal"),
                    "unknown": if_exists(elem, "unknown"),
                },
                "source": "hydroquebec.com",
            }


def fetch_consumption(zone_key="CA-QC", session=None, logger=None):
    data = _fetch_quebec_consumption()
    for elem in reversed(data["details"]):
        if "demandeTotal" in elem["valeurs"]:
            return {
                "zoneKey": zone_key,
                "datetime": elem["date"],
                "consumption": elem["valeurs"]["demandeTotal"],
                "source": "hydroquebec.com",
            }


def fetch_price(zone_key='CA-QC', session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known power price of a given region, country, province, state, or territory."""
    pass

def fetch_exchange(zone_key1='CA-QC', session=None, target_datetime=None, logger=None) -> dict:
    pass


def _fetch_quebec_production() -> str:
    response = requests.get(PRODUCTION_URL)

    if not response.ok:
        pass
    return response.json()


def _fetch_quebec_consumption() -> str:
    response = requests.get(CONSUMPTION_URL)

    if not response.ok:
        pass
    return response.json()


def _to_english(data: str) -> str:

    MAP_GENERATION = {
        "hydraulique": "hydro",
        "thermique": "thermal",
        "solaire": "solar",
        "eolien": "wind",
        "autres": "other",
        "valeurs": "values",
    }

    for k, v in MAP_GENERATION.items():
        data = data.replace(k, v)

    return data

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint
    import logging
    test_logger = logging.getLogger()
    pprint(fetch_consumption(logger=None))

    print('fetch_production() ->')
    pprint(fetch_production(logger=test_logger))

    print('fetch_consumption() ->')
    pprint(fetch_consumption(logger=test_logger))
