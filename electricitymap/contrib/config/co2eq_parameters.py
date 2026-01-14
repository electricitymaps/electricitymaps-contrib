"""Contains a function to make co2eq parameter dicts from
config read from defaults.yaml and zones/*.yaml.
"""

from typing import Any

from electricitymap.contrib.types import ZoneKey


def generate_co2eq_parameters(
    defaults: dict[str, Any], zones_config: dict[ZoneKey, Any]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Returns dicts with co2eq parameters.

    Args:
      defaults: config read from defaults.yaml
      zones_config: config read from zones/*.yaml

    Returns:
        co2eq_parameters_all: dict with co2eq parameters that apply to all zones
        co2eq_parameters_direct: dict with co2eq parameters that apply to direct emissions
        co2eq_parameters_lifecycle: dict with co2eq parameters that apply to lifecycle emissions
    """
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

    # Populate zone overrides.
    for zone_key, zone_config in zones_config.items():
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

    return co2eq_parameters_all, co2eq_parameters_direct, co2eq_parameters_lifecycle
