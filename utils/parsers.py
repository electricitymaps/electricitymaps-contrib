import importlib

from utils.config import ZONES_CONFIG, EXCHANGES_CONFIG

# Prepare all parsers
CONSUMPTION_PARSERS = {}
PRODUCTION_PARSERS = {}
PRODUCTION_PER_UNIT_PARSERS = {}
EXCHANGE_PARSERS = {}
PRICE_PARSERS = {}
CONSUMPTION_FORECAST_PARSERS = {}
GENERATION_FORECAST_PARSERS = {}
EXCHANGE_FORECAST_PARSERS = {}

PARSER_KEY_TO_DICT = {
    'consumption': CONSUMPTION_PARSERS,
    'production': PRODUCTION_PARSERS,
    'productionPerUnit': PRODUCTION_PER_UNIT_PARSERS,
    'exchange': EXCHANGE_PARSERS,
    'price': PRICE_PARSERS,
    'consumptionForecast': CONSUMPTION_FORECAST_PARSERS,
    'generationForecast': GENERATION_FORECAST_PARSERS,
    'exchangeForecast': EXCHANGE_FORECAST_PARSERS
}

# Read all zones
for zone_id, zone_config in ZONES_CONFIG.items():
    for parser_key, v in zone_config.get('parsers', {}).items():
        mod_name, fun_name = v.split('.')
        mod = importlib.import_module('parsers.%s' % mod_name)
        PARSER_KEY_TO_DICT[parser_key][zone_id] = getattr(mod, fun_name)

# Read all exchanges
for exchange_id, exchange_config in EXCHANGES_CONFIG.items():
    for parser_key, v in exchange_config.get('parsers', {}).items():
        mod_name, fun_name = v.split('.')
        mod = importlib.import_module('parsers.%s' % mod_name)
        PARSER_KEY_TO_DICT[parser_key][exchange_id] = getattr(mod, fun_name)
