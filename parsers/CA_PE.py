#!/usr/bin/env python3

import json

# The arrow library is used to handle datetimes consistently with other parsers
import arrow

# The request library is used to fetch content through HTTP
import requests

timezone = "Canada/Atlantic"


def _find_pei_key(pei_list, sought_key):
    matching_item = [
        item
        for item in pei_list
        if "header" in item["data"] and item["data"]["header"].startswith(sought_key)
    ]

    if not matching_item:
        return None

    return matching_item[0]["data"]["actualValue"]


def _get_pei_info(requests_obj):
    url = "https://wdf.princeedwardisland.ca/api/workflow"
    request = {"featureName": "WindEnergy", "queryName": "WindEnergy"}
    headers = {"Content-Type": "application/json"}
    response = requests_obj.post(url, data=json.dumps(request), headers=headers)

    raw_data = response.json().get("data") or []

    datetime_item = [
        item["data"]["text"] for item in raw_data if "text" in item["data"]
    ]
    if not datetime_item:
        # unable to get a timestamp, return empty
        return None
    datetime_text = datetime_item[0][len("Last updated ") :]
    data_timestamp = arrow.get(datetime_text, "MMMM D, YYYY HH:mm A").replace(
        tzinfo="Canada/Atlantic"
    )

    # see https://ruk.ca/content/new-api-endpoint-pei-wind for more info
    data = {
        "pei_load": _find_pei_key(raw_data, "Total On-Island Load"),
        "pei_wind_gen": _find_pei_key(raw_data, "Total On-Island Wind Generation"),
        "pei_fossil_gen": _find_pei_key(
            raw_data, "Total On-Island Fossil Fuel Generation"
        ),
        "pei_wind_used": _find_pei_key(raw_data, "Wind Power Used On Island"),
        "pei_wind_exported": _find_pei_key(raw_data, "Wind Power Exported Off Island"),
        "datetime": data_timestamp.datetime,
    }

    # the following keys are always required downstream, if we don't have them, no sense returning
    if data["pei_wind_gen"] is None or data["pei_fossil_gen"] is None:
        return None

    return data


def fetch_production(
    zone_key="CA-PE", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()
    pei_info = _get_pei_info(requests_obj)

    if pei_info is None:
        return None

    data = {
        "datetime": pei_info["datetime"],
        "zoneKey": zone_key,
        "production": {
            "wind": pei_info["pei_wind_gen"],
            # These are oil-fueled ("heavy fuel oil" and "diesel") generators
            # used as peakers and back-up
            "oil": pei_info["pei_fossil_gen"],
            # specify some sources that definitely aren't present on PEI as zero,
            # this allows the analyzer to better estimate CO2eq
            "coal": 0,
            "hydro": 0,
            "nuclear": 0,
            "geothermal": 0,
        },
        "storage": {},
        "source": "princeedwardisland.ca",
    }

    return data


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys != "CA-NB->CA-PE":
        raise NotImplementedError("This exchange pair is not implemented")

    requests_obj = session or requests.session()
    pei_info = _get_pei_info(requests_obj)

    if pei_info is None or pei_info["pei_load"] is None:
        return None

    # PEI imports most of its electricity. Everything not generated on island
    # is imported from New Brunswick.
    # In case of wind, some is paper-"exported" even if there is a net import,
    # and 'pei_wind_used'/'data5' indicates their accounting of part of the load
    # served by non-exported wind.
    # https://www.princeedwardisland.ca/en/feature/pei-wind-energy says:
    # "Wind Power Exported Off-Island is that portion of wind generation that is supplying
    # contracts elsewhere. The actual electricity from this portion of wind generation
    # may stay within PEI but is satisfying a contractual arrangement in another jurisdiction."
    # We are ignoring these paper exports, as they are an accounting/legal detail
    # that doesn't actually reflect what happens on the wires.
    # (New Brunswick being the only interconnection with PEI, "exporting" wind power to NB
    # then "importing" a balance of NB electricity likely doesn't actually happen.)
    imported_from_nb = (
        pei_info["pei_load"] - pei_info["pei_fossil_gen"] - pei_info["pei_wind_gen"]
    )

    # In expected result, "net" represents an export.
    # We have sorted_zone_keys 'CA-NB->CA-PE', so it's export *from* NB,
    # and import *to* PEI.
    data = {
        "datetime": pei_info["datetime"],
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": imported_from_nb,
        "source": "princeedwardisland.ca",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print('fetch_exchange("CA-PE", "CA-NB") ->')
    print(fetch_exchange("CA-PE", "CA-NB"))
