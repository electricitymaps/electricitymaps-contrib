from typing import Any, Dict

from ruamel.yaml import YAML

from electricitymap.contrib.config.constants import EXCHANGE_FILENAME_ZONE_SEPARATOR
from electricitymap.contrib.lib.types import ZoneKey

yaml = YAML(typ="safe")


def read_defaults(config_dir) -> Dict[str, Any]:
    """Reads the defaults.yaml file."""
    defaults_path = config_dir.joinpath("defaults.yaml")
    return yaml.load(open(defaults_path, encoding="utf-8"))


def read_zones_config(config_dir) -> Dict[ZoneKey, Any]:
    """Reads all the zone config files."""
    zones_config: Dict[ZoneKey, Any] = {}
    for zone_path in config_dir.joinpath("zones").glob("*.yaml"):
        zone_key = ZoneKey(zone_path.stem)
        zones_config[zone_key] = yaml.load(open(zone_path, encoding="utf-8"))
    return zones_config


def read_exchanges_config(config_dir) -> Dict[str, Any]:
    """Reads all the exchange config files."""
    exchanges_config = {}
    for exchange_path in config_dir.joinpath("exchanges").glob("*.yaml"):
        exchange_key_unicode = exchange_path.stem
        zone_keys = exchange_key_unicode.split(EXCHANGE_FILENAME_ZONE_SEPARATOR)
        assert len(zone_keys) == 2
        exchange_key = "->".join(zone_keys)
        exchanges_config[exchange_key] = yaml.load(
            open(exchange_path, encoding="utf-8")
        )
    return exchanges_config
