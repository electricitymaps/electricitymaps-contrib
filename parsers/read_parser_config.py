import importlib
import json
import os


def relative_path(script_reference_path, rel_path):
    # __file__ should be passed as script_reference_path
    script_path = os.path.abspath(
        script_reference_path)  # i.e. /path/to/dir/foobar.py
    script_dir = os.path.split(script_path)[0]  # i.e. /path/to/dir/
    return os.path.join(script_dir, rel_path)


# Prepare zone bounding boxes
ZONE_BOUNDING_BOXES = {}

# Read parser import list from config jsons
zones_config = json.load(open(relative_path(
    __file__, '../config/zones.json')))

# Read all zones
for zone_id, zone_config in zones_config.items():
    if 'bounding_box' in zone_config:
        ZONE_BOUNDING_BOXES[zone_id] = zone_config['bounding_box']

# Prepare all parsers
CONSUMPTION_PARSERS = {}
PRODUCTION_PARSERS = {}
PRODUCTION_PER_UNIT_PARSERS = {}
EXCHANGE_PARSERS = {}
PRICE_PARSERS = {}
CONSUMPTION_FORECAST_PARSERS = {}
GENERATION_FORECAST_PARSERS = {}
EXCHANGE_FORECAST_PARSERS = {}

# Read parser import list from config jsons
zones_config = json.load(open(relative_path(
    __file__, '../config/zones.json')))
exchanges_config = json.load(open(relative_path(
    __file__, '../config/exchanges.json')))
zone_neighbours = {}
for k, v in exchanges_config.items():
    zone_names = k.split('->')
    pairs = [
        (zone_names[0], zone_names[1]),
        (zone_names[1], zone_names[0])
    ]
    for zone_name_1, zone_name_2 in pairs:
        if zone_name_1 not in zone_neighbours:
            zone_neighbours[zone_name_1] = set()
        zone_neighbours[zone_name_1].add(zone_name_2)

parser_key_to_dict = {
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
for zone_id, zone_config in zones_config.items():
    for parser_key, v in zone_config.get('parsers', {}).items():
        mod_name, fun_name = v.split('.')
        mod = importlib.import_module('electricitymap.parsers.%s' % mod_name)
        parser_key_to_dict[parser_key][zone_id] = getattr(mod, fun_name)

# Read all exchanges
for exchange_id, exchange_config in exchanges_config.items():
    for parser_key, v in exchange_config.get('parsers', {}).items():
        mod_name, fun_name = v.split('.')
        mod = importlib.import_module('electricitymap.parsers.%s' % mod_name)
        parser_key_to_dict[parser_key][exchange_id] = getattr(mod, fun_name)
