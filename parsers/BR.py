from collections import defaultdict

import arrow
import requests

from .lib.validation import validate

URL = "http://tr.ons.org.br/Content/GetBalancoEnergetico/null"
SOURCE = "ons.org.br"

GENERATION_MAPPING = {
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


def get_data(session):
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
    entries_to_remove = {"hidraulica", "itaipu50HzBrasil", "itaipu60Hz", "total"}
    mapped_totals = {
        GENERATION_MAPPING.get(name, "unknown"): val
        for name, val in totals.items()
        if name not in entries_to_remove
    }

    return dt, mapped_totals


def fetch_production(zone_key, session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    timestamp, production = production_processor(data, zone_key)

    datapoint = {
        "zoneKey": zone_key,
        "datetime": timestamp.datetime,
        "production": production,
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

    data = get_data(session)
    dt = arrow.get(data["Data"]).datetime
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    country_exchange = COUNTRIES_EXCHANGE.get(zone_key1) or COUNTRIES_EXCHANGE.get(
        zone_key2
    )

    net_flow = (
        data["internacional"][country_exchange["name"]] * country_exchange["flow"]
    )

    return {
        "datetime": dt,
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": net_flow,
        "source": SOURCE,
    }


def fetch_region_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two Brazilian regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    data = get_data(session)
    dt = arrow.get(data["Data"]).datetime
    sorted_regions = "->".join(sorted([zone_key1, zone_key2]))

    exchange = REGION_EXCHANGES[sorted_regions]
    net_flow = (
        data["intercambio"][exchange] * REGION_EXCHANGES_DIRECTIONS[sorted_regions]
    )

    return {
        "datetime": dt,
        "sortedZoneKeys": sorted_regions,
        "netFlow": net_flow,
        "source": SOURCE,
    }


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
