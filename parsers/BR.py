from collections import defaultdict
from parsers.BD import GENERATION_MAPPING

import arrow
import requests

from .lib.validation import validate


URL = "http://tr.ons.org.br/Content/GetBalancoEnergetico/null"
SOURCE = "ons.org.br"

GENERATION_MAPPINGE = {
    "nuclear": "nuclear",
    "eolica": "wind",
    "termica": "unknown",
    "solar": "solar",
    "hydro": "hydro",
}

REGIONS = {
    "BR-NE": "nordeste",
    "BR-N": "norte",
    "BR-CS": "sudesteECentroOeste",
    "BR-S": "sul",
}

REGION_EXCHANGES = {
    "BR-CS->BR-S": "sul_sudeste",
    "BR-CS->BR-NE": "sudeste_nordeste",
    "BR-CS->BR-N": "sudeste_norteFic",
    "BR-N->BR-NE": "norteFic_nordeste",
}


REGION_EXCHANGES_DIRECTIONS = {
    "BR-CS->BR-S": -1,
    "BR-CS->BR-NE": 1,
    "BR-CS->BR-N": 1,
    "BR-N->BR-NE": 1,
}

COUNTRIES_EXCHANGE = {
    "UY": {"name": "uruguai", "flow": 1},
    "AR": {"name": "argentina", "flow": -1},
    "PY": {"name": "paraguai", "flow": -1},
}


def get_data(session, logger):
    """Requests generation data in json format."""
    s = session or requests.session()
    json_data = s.get(URL).json()

    return json_data


def production_processor(json_data, zone_key) -> tuple:
    """Extracts data timestamp and sums regional data into totals by key."""

    dt = arrow.get(json_data["Data"])
    totals = defaultdict(lambda: 0.0)

    region = REGIONS[zone_key]
    breakdown = json_data[region]["geracao"]
    for generation, val in breakdown.items():
        totals[generation] += val

    # BR_CS contains the Itaipu Dam.
    # We merge the hydro keys into one, then remove unnecessary keys.
    totals["hydro"] = (
        totals.get("hidraulica", 0.0)
        + totals.get("itaipu50HzBrasil", 0.0)
        + totals.get("itaipu60Hz", 0.0)
    )
    entries_to_remove = ("hidraulica", "itaipu50HzBrasil", "itaipu60Hz", "total")
    for k in entries_to_remove:
        totals.pop(k, None)

    mapped_totals = {
        GENERATION_MAPPING.get(name, "unknown"): val for name, val in totals.items()
    }

    return dt, mapped_totals


def fetch_production(zone_key, session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    gd = get_data(session, logger)
    generation = production_processor(gd, zone_key)

    datapoint = {
        "zoneKey": zone_key,
        "datetime": generation[0].datetime,
        "production": generation[1],
        "storage": {
            "hydro": None,
        },
        "source": SOURCE,
    }

    datapoint = validate(
        datapoint, logger, remove_negative=True, required=["hydro"], floor=1000
    )

    return datapoint


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    gd = get_data(session, logger)

    if zone_key1 in COUNTRIES_EXCHANGE.keys():
        country_exchange = COUNTRIES_EXCHANGE[zone_key1]

    if zone_key2 in COUNTRIES_EXCHANGE.keys():
        country_exchange = COUNTRIES_EXCHANGE[zone_key2]

    return {
        "datetime": arrow.get(gd["Data"]).datetime,
        "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
        "netFlow": gd["internacional"][country_exchange["name"]]
        * country_exchange["flow"],
        "source": SOURCE,
    }


def fetch_region_exchange(
    region1, region2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two Brazilian regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    gd = get_data(session, logger)
    dt = arrow.get(gd["Data"]).datetime
    scc = "->".join(sorted([region1, region2]))

    exchange = REGION_EXCHANGES[scc]
    nf = gd["intercambio"][exchange] * REGION_EXCHANGES_DIRECTIONS[scc]

    return {"datetime": dt, "sortedZoneKeys": scc, "netFlow": nf, "source": SOURCE}


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production(BR-NE) ->")
    print(fetch_production("BR-NE"))

    print("fetch_production(BR-N) ->")
    print(fetch_production("BR-N"))

    print("fetch_production(BR-CS) ->")
    print(fetch_production("BR-CS"))

    print("fetch_production(BR-S) ->")
    print(fetch_production("BR-S"))

    print("fetch_exchange(BR-S, UY) ->")
    print(fetch_exchange("BR-S", "UY"))

    print("fetch_exchange(BR-S, AR) ->")
    print(fetch_exchange("BR-S", "AR"))

    print("fetch_region_exchange(BR-CS->BR-S)")
    print(fetch_region_exchange("BR-CS", "BR-S"))

    print("fetch_region_exchange(BR-CS->BR-NE)")
    print(fetch_region_exchange("BR-CS", "BR-NE"))

    print("fetch_region_exchange(BR-CS->BR-N)")
    print(fetch_region_exchange("BR-CS", "BR-N"))

    print("fetch_region_exchange(BR-N->BR-NE)")
    print(fetch_region_exchange("BR-N", "BR-NE"))
