from glob import glob
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

defaults = yaml.safe_load(open(CONFIG_DIR.joinpath("defaults.yaml"), encoding="utf-8"))

zones = {}
for zone_path in CONFIG_DIR.joinpath("zones").glob("*.yaml"):
    zone_key = zone_path.stem
    zones[zone_key] = yaml.safe_load(open(zone_path, encoding="utf-8"))

exchanges = {}
for exchange_path in CONFIG_DIR.joinpath("exchanges").glob("*.yaml"):
    exchange_key = exchange_path.stem
    exchanges[exchange_key] = yaml.safe_load(open(exchange_path, encoding="utf-8"))


co2eq_parameters_all = {
    k: {
        "defaults": defaults[k],
        "zoneOverrides": {},
    }
    for k in ["fallbackZoneMixes", "isLowCarbon", "isRenewable"]
}
co2eq_parameters_direct = {
    "emissionFactors": {
        "defaults": defaults["emissionFactors"]["direct"],
        "zoneOverrides": {},
    },
}
co2eq_parameters_lifecycle = {
    "emissionFactors": {
        "defaults": defaults["emissionFactors"]["lifecycle"],
        "zoneOverrides": {},
    },
}
# Populate zone overrides
for zone_key, zone_config in zones.items():
    for k in ["fallbackZoneMixes", "isLowCarbon", "isRenewable"]:
        if k in zone_config:
            co2eq_parameters_all[k]["zoneOverrides"][zone_key] = zone_config[k]
            del zone_config[k]
    if "emissionFactors" in zone_config:
        for k in ["direct", "lifecycle"]:
            if k in zone_config["emissionFactors"]:
                co2eq_parameters_direct["emissionFactors"]["zoneOverrides"][
                    zone_key
                ] = zone_config["emissionFactors"][k]
                del zone_config["emissionFactors"][k]
            if k in zone_config["emissionFactors"]:
                co2eq_parameters_lifecycle["emissionFactors"]["zoneOverrides"][
                    zone_key
                ] = zone_config["emissionFactors"][k]
                del zone_config["emissionFactors"][k]


co2eq_parameters_direct = {**co2eq_parameters_all, **co2eq_parameters_direct}
co2eq_parameters_lifecycle = {**co2eq_parameters_all, **co2eq_parameters_lifecycle}


breakpoint()
