import json
from copy import deepcopy
from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).parent.parent.parent.parent.joinpath("config").resolve()

# Read JSON files
ZONES_CONFIG = json.load(open(CONFIG_DIR.joinpath("zones.json"), encoding="utf-8"))
EXCHANGES_CONFIG = json.load(
    open(CONFIG_DIR.joinpath("exchanges.json"), encoding="utf-8")
)
CO2EQ_PARAMETERS_ALL = json.load(
    open(CONFIG_DIR.joinpath("co2eq_parameters_all.json"), encoding="utf-8")
)
CO2EQ_PARAMETERS_LIFECYCLE = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(
        open(CONFIG_DIR.joinpath("co2eq_parameters_lifecycle.json"), encoding="utf-8")
    ),
}
CO2EQ_PARAMETERS_DIRECT = {
    **CO2EQ_PARAMETERS_ALL,
    **json.load(
        open(CONFIG_DIR.joinpath("co2eq_parameters_direct.json"), encoding="utf-8")
    ),
}
CO2EQ_PARAMETERS = CO2EQ_PARAMETERS_LIFECYCLE  # Global LCA is the default


exchanges = {e_k: EXCHANGES_CONFIG[e_k] for e_k in EXCHANGES_CONFIG}

# Generate individual yaml config files for exchanges
for exchange_key, exchange_config in exchanges.items():
    with open(
        CONFIG_DIR.joinpath(f"exchanges/{exchange_key}.yaml"), "w", encoding="utf-8"
    ) as f:
        f.write(yaml.dump(exchange_config, default_flow_style=False))

zones = {z_k: ZONES_CONFIG[z_k] for z_k in ZONES_CONFIG}

# Generate individual yaml config files for zones
for zone_key, zone_config in zones.items():
    _zone_config = deepcopy(zone_config)
    # co2eq parameters all
    fields = ["fallbackZoneMixes", "isLowCarbon", "isRenewable"]
    for field in fields:
        if zone_key in CO2EQ_PARAMETERS[field]["zoneOverrides"]:
            _zone_config[field] = CO2EQ_PARAMETERS[field]["zoneOverrides"][zone_key]
    # emission factors
    if zone_key in CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["zoneOverrides"]:
        _zone_config["emissionFactors"] = {
            "direct": CO2EQ_PARAMETERS_DIRECT["emissionFactors"]["zoneOverrides"][
                zone_key
            ]
        }
    if zone_key in CO2EQ_PARAMETERS_LIFECYCLE["emissionFactors"]["zoneOverrides"]:
        e_f = _zone_config["emissionFactors"] if "emissionFactors" in _zone_config else {}
        e_f["lifecycle"] = CO2EQ_PARAMETERS_LIFECYCLE["emissionFactors"]["zoneOverrides"][
            zone_key
        ]
        _zone_config["emissionFactors"] = e_f
    with open(
        CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml"), "w", encoding="utf-8"
    ) as f:
        f.write(yaml.dump(_zone_config, default_flow_style=False))
