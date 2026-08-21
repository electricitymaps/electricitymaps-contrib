import json
from typing import Any

from ruamel.yaml import YAML

from electricitymap.contrib.config.constants import EXCHANGE_FILENAME_ZONE_SEPARATOR
from electricitymap.contrib.types import ZoneKey

yaml = YAML(typ="safe")


def read_defaults(config_dir) -> dict[str, Any]:
    """Reads the defaults.yaml file."""
    defaults_path = config_dir.joinpath("defaults.yaml")
    with open(defaults_path, encoding="utf-8") as file:
        return yaml.load(file)


def read_zones_config(config_dir, retired=False) -> dict[ZoneKey, Any]:
    """Reads all the zone config files."""
    zones_config: dict[ZoneKey, Any] = {}
    for zone_path in config_dir.joinpath(
        "retired_zones" if retired is True else "zones"
    ).glob("*.yaml"):
        try:
            zone_key = ZoneKey(zone_path.stem)
            with open(zone_path, encoding="utf-8") as file:
                zones_config[zone_key] = yaml.load(file)
        except Exception as e:
            print(f"Error reading zone config for {zone_path.stem}: {e}")
    return zones_config


def read_exchanges_config(config_dir) -> dict[ZoneKey, Any]:
    """Reads all the exchange config files."""
    exchanges_config = {}
    for exchange_path in config_dir.joinpath("exchanges").glob("*.yaml"):
        exchange_key_unicode = exchange_path.stem
        zone_keys = exchange_key_unicode.split(EXCHANGE_FILENAME_ZONE_SEPARATOR)
        assert len(zone_keys) == 2
        exchange_key = "->".join(zone_keys)
        with open(exchange_path, encoding="utf-8") as file:
            exchanges_config[exchange_key] = yaml.load(file)
    return exchanges_config


def read_data_centers_config(config_dir):
    """Reads the data centers config file."""
    from electricitymap.contrib.config.data_center_model import DataCenters

    data_centers_path = config_dir.joinpath("data_centers", "data_centers.json")
    with open(data_centers_path, encoding="utf-8") as file:
        data_centers_dict = json.load(file)
    return DataCenters(data_centers=list(data_centers_dict.values()))
