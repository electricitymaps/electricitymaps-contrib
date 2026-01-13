import importlib

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG
from electricitymap.types import ParserDataType

# Prepare all parsers
CONSUMPTION_PARSERS = {}
PRODUCTION_PARSERS = {}
PRODUCTION_PER_MODE_FORECAST_PARSERS = {}
EXCHANGE_PARSERS = {}
PRICE_PARSERS = {}
PRICE_INTRADAY_PARSERS = {}
CONSUMPTION_FORECAST_PARSERS = {}
GENERATION_FORECAST_PARSERS = {}
EXCHANGE_FORECAST_PARSERS = {}
PRODUCTION_CAPACITY_PARSERS = {}
DAYAHEAD_LOCATIONAL_MARGINAL_PRICE_PARSERS = {}
REALTIME_LOCATIONAL_MARGINAL_PRICE_PARSERS = {}
GRID_ALERTS_PARSERS = {}
# TODO remove
PRODUCTION_PER_UNIT_PARSERS = {}

PARSER_DATA_TYPE_TO_DICT = {
    ParserDataType.CONSUMPTION: CONSUMPTION_PARSERS,
    ParserDataType.CONSUMPTION_FORECAST: CONSUMPTION_FORECAST_PARSERS,
    ParserDataType.DAYAHEAD_LOCATIONAL_MARGINAL_PRICE: DAYAHEAD_LOCATIONAL_MARGINAL_PRICE_PARSERS,
    ParserDataType.EXCHANGE: EXCHANGE_PARSERS,
    ParserDataType.EXCHANGE_FORECAST: EXCHANGE_FORECAST_PARSERS,
    ParserDataType.GENERATION_FORECAST: GENERATION_FORECAST_PARSERS,
    ParserDataType.PRICE: PRICE_PARSERS,
    ParserDataType.PRICE_INTRADAY: PRICE_INTRADAY_PARSERS,
    ParserDataType.PRODUCTION: PRODUCTION_PARSERS,
    ParserDataType.PRODUCTION_PER_MODE_FORECAST: PRODUCTION_PER_MODE_FORECAST_PARSERS,
    ParserDataType.REALTIME_LOCATIONAL_MARGINAL_PRICE: REALTIME_LOCATIONAL_MARGINAL_PRICE_PARSERS,
    ParserDataType.PRODUCTION_CAPACITY: PRODUCTION_CAPACITY_PARSERS,
    ParserDataType.GRID_ALERTS: GRID_ALERTS_PARSERS,
}


def _parser_key_to_parser_folder(parser_key: ParserDataType):
    CAPACITY_PARSERS_FOLDER = "electricitymap.contrib.capacity_parsers"
    DEFAULT_PARSERS_FOLDER = "electricitymap.contrib.parsers"
    return (
        CAPACITY_PARSERS_FOLDER
        if parser_key == ParserDataType.PRODUCTION_CAPACITY
        else DEFAULT_PARSERS_FOLDER
    )


# Read all zones
for zone_id, zone_config in ZONES_CONFIG.items():
    for parser_key, v in zone_config.get("parsers", {}).items():
        mod_name, fun_name = v.split(".")
        try:
            _parser_key = ParserDataType(parser_key)
        except ValueError:
            raise ValueError(
                f"Invalid parser key: {parser_key} for zone: {zone_id}"
            ) from None
        mod = importlib.import_module(
            f"{_parser_key_to_parser_folder(_parser_key)}.{mod_name}"
        )
        PARSER_DATA_TYPE_TO_DICT[_parser_key][zone_id] = getattr(mod, fun_name)


# Read all exchanges
for exchange_id, exchange_config in EXCHANGES_CONFIG.items():
    for parser_key, v in exchange_config.get("parsers", {}).items():
        try:
            _parser_key = ParserDataType(parser_key)
        except ValueError:
            raise ValueError(
                f"Invalid parser key: {parser_key} for exchange: {exchange_id}"
            ) from None
        mod_name, fun_name = v.split(".")
        mod = importlib.import_module(
            f"{_parser_key_to_parser_folder(_parser_key)}.{mod_name}"
        )
        PARSER_DATA_TYPE_TO_DICT[_parser_key][exchange_id] = getattr(mod, fun_name)
