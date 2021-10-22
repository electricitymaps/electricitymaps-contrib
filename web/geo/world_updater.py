import json

import pycountry

WORLD_PATH = "new_world.geojson"


class Country:
    def __init__(self, alpha_2: str, name: str):
        self.alpha_2 = alpha_2
        self.name = name


def match_zone_to_country(zone_key: str) -> object:
    zones_manual_overrides = {
        "XX": "CY",
        "NKR": "AZ",
    }
    if zone_key in zones_manual_overrides:
        zk = zones_manual_overrides[zone_key]
    else:
        zk = zone_key[:2]
    country = pycountry.countries.get(alpha_2=zk)
    if country is None:
        countries_manual_override = {
            "XK": Country("XK", "Kosovo"),
        }
        if zone_key in countries_manual_override:
            return countries_manual_override[zone_key]
        else:
            print("Suggestions?")
            print(pycountry.countries.search_fuzzy(zk))
            raise ValueError(f"No country found for zone: {zone_key}")
    return country


def update_world():
    with open(WORLD_PATH, "r") as f:
        world = json.load(f)

    for feature in world["features"]:
        if "zoneName" not in feature["properties"]:
            raise KeyError(
                f"zoneName not in feature properties for id: {feature['properties']['id']}"
            )
        if feature["properties"]["zoneName"] != feature["properties"]["id"]:
            raise ValueError(
                f"zoneName does not match id for: {feature['properties']['id']}"
            )
        country = match_zone_to_country(feature["properties"]["zoneName"])
        feature["properties"]["countryKey"] = country.alpha_2
        feature["properties"]["countryName"] = country.name
        del feature["properties"]["id"]

    with open("_new_world.geojson", "w") as f:
        json.dump(world, f)
