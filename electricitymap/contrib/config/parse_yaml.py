from pathlib import Path

import yaml
from deepdiff import DeepDiff

from electricitymap.contrib.config import (
    CO2EQ_PARAMETERS_DIRECT,
    CO2EQ_PARAMETERS_LIFECYCLE,
    EXCHANGES_CONFIG,
    ZONES_CONFIG,
)

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

defaults = yaml.safe_load(open(CONFIG_DIR.joinpath("defaults.yaml"), encoding="utf-8"))

zones = {}
for zone_path in CONFIG_DIR.joinpath("zones").glob("*.yaml"):
    zone_key = zone_path.stem
    zones[zone_key] = yaml.safe_load(open(zone_path, encoding="utf-8"))

exchanges = {}
for exchange_path in CONFIG_DIR.joinpath("exchanges").glob("*.yaml"):
    _exchange_key_unicode = exchange_path.stem
    exchange_key = "->".join(_exchange_key_unicode.split("→"))
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
                if k == "direct":
                    co2eq_parameters_direct["emissionFactors"]["zoneOverrides"][
                        zone_key
                    ] = zone_config["emissionFactors"][k]
                elif k == "lifecycle":
                    co2eq_parameters_lifecycle["emissionFactors"]["zoneOverrides"][
                        zone_key
                    ] = zone_config["emissionFactors"][k]
        del zone_config["emissionFactors"]


co2eq_parameters_direct = {**co2eq_parameters_all, **co2eq_parameters_direct}
co2eq_parameters_lifecycle = {**co2eq_parameters_all, **co2eq_parameters_lifecycle}

zone_diff = DeepDiff(zones, ZONES_CONFIG)
assert zone_diff == {}, f"Zones config does not match: {list(zone_diff.values())[0]}"
exchange_diff = DeepDiff(exchanges, EXCHANGES_CONFIG)
assert (
    exchange_diff == {}
), f"Exchanges config does not match: {list(exchange_diff.values())[0]}"
co2eq_parameters_direct_diff = DeepDiff(
    co2eq_parameters_direct, CO2EQ_PARAMETERS_DIRECT
)
assert (
    co2eq_parameters_direct_diff == {}
), f"CO2EQ parameters direct config does not match: {list(co2eq_parameters_direct_diff.values())[0]}"
co2eq_parameters_lifecycle_diff = DeepDiff(
    co2eq_parameters_lifecycle, CO2EQ_PARAMETERS_LIFECYCLE
)
assert (
    co2eq_parameters_lifecycle_diff == {}
), f"CO2EQ parameters lifecycle config does not match: {list(co2eq_parameters_lifecycle_diff.values())[0]}"


print("💪 All good!")
