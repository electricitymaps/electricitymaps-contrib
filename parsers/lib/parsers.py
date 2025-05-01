import importlib

from electricitymap.contrib.lib.data_types import ParserDataType
from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG

# Prepare all parsers
CONSUMPTION_PARSERS = {}
PRODUCTION_PARSERS = {}
PRODUCTION_PER_MODE_FORECAST_PARSERS = {}
PRODUCTION_PER_UNIT_PARSERS = {}
EXCHANGE_PARSERS = {}
PRICE_PARSERS = {}
CONSUMPTION_FORECAST_PARSERS = {}
GENERATION_FORECAST_PARSERS = {}
EXCHANGE_FORECAST_PARSERS = {}
PRODUCTION_CAPACITY_PARSERS = {}
DAYAHEAD_LOCATIONAL_MARGINAL_PRICE_PARSERS = {}
REALTIME_LOCATIONAL_MARGINAL_PRICE_PARSERS = {}

PARSER_DATA_TYPE_TO_DICT = {
    ParserDataType.CONSUMPTION: CONSUMPTION_PARSERS,
    ParserDataType.CONSUMPTION_FORECAST: CONSUMPTION_FORECAST_PARSERS,
    ParserDataType.DAYAHEAD_LOCATIONAL_MARGINAL_PRICE: DAYAHEAD_LOCATIONAL_MARGINAL_PRICE_PARSERS,
    ParserDataType.EXCHANGE: EXCHANGE_PARSERS,
    ParserDataType.EXCHANGE_FORECAST: EXCHANGE_FORECAST_PARSERS,
    ParserDataType.GENERATION_FORECAST: GENERATION_FORECAST_PARSERS,
    ParserDataType.PRICE: PRICE_PARSERS,
    ParserDataType.PRODUCTION: PRODUCTION_PARSERS,
    ParserDataType.PRODUCTION_PER_MODE_FORECAST: PRODUCTION_PER_MODE_FORECAST_PARSERS,
    ParserDataType.REALTIME_LOCATIONAL_MARGINAL_PRICE: REALTIME_LOCATIONAL_MARGINAL_PRICE_PARSERS,
    ParserDataType.PRODUCTION_CAPACITY: PRODUCTION_CAPACITY_PARSERS,
}


def _parser_key_to_parser_folder(parser_key: str):
    return (
        "electricitymap.contrib.capacity_parsers"
        if parser_key == "productionCapacity"
        else "parsers"
    )


# Read all zones
for zone_id, zone_config in ZONES_CONFIG.items():
    for parser_key, v in zone_config.get("parsers", {}).items():
        mod_name, fun_name = v.split(".")
        mod = importlib.import_module(
            f"{_parser_key_to_parser_folder(parser_key)}.{mod_name}"
        )
        PARSER_DATA_TYPE_TO_DICT[parser_key][zone_id] = getattr(mod, fun_name)


# Read all exchanges
for exchange_id, exchange_config in EXCHANGES_CONFIG.items():
    for parser_key, v in exchange_config.get("parsers", {}).items():
        mod_name, fun_name = v.split(".")
        mod = importlib.import_module(f"parsers.{mod_name}")
        PARSER_DATA_TYPE_TO_DICT[parser_key][exchange_id] = getattr(mod, fun_name)
