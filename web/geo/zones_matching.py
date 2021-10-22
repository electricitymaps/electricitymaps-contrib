import json

import pytz

from ...scripts.utils import JsonFilePatcher

WORLD_PATH = "new_world.geojson"
ZONES_PATH = "../../config/zones.json"
FLAGS_PATH = "../public/images/flag-icons/flags_iso/list.txt"


def match_zones():
    zones = json.load(open(ZONES_PATH))
    world = json.load(open(WORLD_PATH))
    flags = [f.replace(".png", "") for f in open(FLAGS_PATH).read().split("\n")]
    for ft in world["features"]:
        zone_name = ft["properties"]["zoneName"]
        if zone_name not in zones.keys():
            tz_overrides = {"HM": "Asia/Karachi"}
            if zone_name in tz_overrides:
                tz = tz_overrides[zone_name]
            else:
                tz = str(pytz.country_timezones(ft["properties"]["countryKey"])[0])

            flag_names = {
                "XX": "_Northern Cyprus.png",
                "AUS-TAS-CBI": "au.png",
                "IN-AN": "in.png",
                "IN-AR": "in.png",
                "IN-AS": "in.png",
                "IN-BR": "in.png",
                "IN-DN": "in.png",
                "IN-GA": "in.png",
                "IN-HR": "in.png",
                "IN-JK": "in.png",
                "IN-JH": "in.png",
                "IN-KL": "in.png",
                "IN-MP": "in.png",
                "IN-MN": "in.png",
                "IN-ML": "in.png",
                "IN-MZ": "in.png",
                "IN-NL": "in.png",
                "IN-OR": "in.png",
                "IN-PY": "in.png",
                "IN-RJ": "in.png",
                "IN-SK": "in.png",
                "IN-TN": "in.png",
                "IN-TR": "in.png",
                "IN-WB": "in.png",
                "MY-EM": "my.png",
                "NZ-NZA": "nz.png",
                "NZ-NZC": "nz.png",
                # Not in flags for some reason
                "TN": "tn.png",
            }
            if zone_name.lower() in flags:
                flag_names[zone_name] = zone_name.lower() + ".png"
            try:
                zone = {
                    "flag_file_name": flag_names[zone_name],
                    "timezone": tz,
                }
            except KeyError:
                print(zone_name, "no flag")
            zones[zone_name] = zone

    with JsonFilePatcher(ZONES_PATH, "w") as f:
        json.dump(zones, f, indent=2, sort_keys=True)
