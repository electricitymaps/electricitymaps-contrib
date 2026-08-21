import json
import os

import yaml


def add_country_names():
    json_path = os.path.join(os.path.dirname(__file__), "../config/zone_names.json")
    zones_dir = os.path.join(os.path.dirname(__file__), "../config/zones")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
        zones = data["zoneShortName"]
    for key, value in zones.items():
        country_name = value.get("countryName") or value.get("zoneName")
        zone_name = value.get("zoneName")
        zone_short_name = value.get("zoneShortName")
        if not country_name:
            print(f"Zone {key} is in the JSON file but has no country name")
            continue
        yaml_path = os.path.join(zones_dir, f"{key}.yaml")
        if not os.path.exists(yaml_path):
            print(f"Zone {key} is in the JSON file but not in the zones directory")
            continue
        with open(yaml_path, encoding="utf-8") as f_yaml:
            try:
                yaml_data = yaml.safe_load(f_yaml)
            except Exception:
                print(f"Error parsing yaml file : {yaml_path}")
                continue
        yaml_data["country_name"] = country_name
        yaml_data["zone_name"] = zone_name
        if zone_short_name:
            yaml_data["zone_short_name"] = zone_short_name
        with open(yaml_path, "w", encoding="utf-8") as f_yaml:
            yaml.dump(yaml_data, f_yaml, allow_unicode=True, sort_keys=False)


def check_additional_attributes():
    zones_dir = os.path.join(os.path.dirname(__file__), "../config/zones")
    zones_without_country_name = []
    zones_without_zone_name = []
    zones_with_zone_short_name = []
    for filename in os.listdir(zones_dir):
        if not filename.endswith(".yaml"):
            continue
        yaml_path = os.path.join(zones_dir, filename)
        with open(yaml_path, encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)
        if "country_name" not in yaml_data:
            zones_without_country_name.append(filename)
        if "zone_name" not in yaml_data:
            zones_without_zone_name.append(filename)
        if "zone_short_name" in yaml_data:
            zones_with_zone_short_name.append(filename)
    print(f"Zones without country_name: {zones_without_country_name}")
    print(f"Zones without zone_name: {zones_without_zone_name}")
    print(f"Zones with zone_short_name: {zones_with_zone_short_name}")


if __name__ == "__main__":
    add_country_names()
    check_additional_attributes()
