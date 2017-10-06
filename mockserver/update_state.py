# This script should be run from the root directory
import arrow, importlib, json, pprint, sys
from random import random
pp = pprint.PrettyPrinter(indent=2)

# Read parser import list from config jsons
zones_config = json.load(open('config/zones.json'))
exchanges_config = json.load(open('config/exchanges.json'))

# Read zone_name from commandline
if not len(sys.argv) > 1:
    raise Exception('Missing argument <zone_name>')
zone_name = sys.argv[1]
zone_config = zones_config[zone_name]

# Find parsers
production_parser = zone_config['parsers']['production']
exchange_parser_keys = []
for k in exchanges_config.keys():
    zones = k.split('->')
    if zone_name in zones: exchange_parser_keys.append(k)

# Import / run production parser
print 'Finding and executing %s production parser %s..' % (zone_name, production_parser)
mod_name, fun_name = production_parser.split('.')
mod = importlib.import_module('parsers.%s' % mod_name)
production = getattr(mod, fun_name)(zone_name)
if type(production) == list: production = production[-1]
pp.pprint(production)

# Import / run exchange parser(s)
exchanges = []
for k in exchange_parser_keys:
    exchange_parser = exchanges_config[k]['parsers']['exchange']
    print 'Finding and executing %s exchange parser %s..' % (k, exchange_parser)
    mod_name, fun_name = exchange_parser.split('.')
    mod = importlib.import_module('parsers.%s' % mod_name)
    sorted_zone_names = sorted(k.split('->'))
    exchange = getattr(mod, fun_name)(sorted_zone_names[0], sorted_zone_names[1])
    if type(exchange) == list: exchange = exchange[-1]
    exchanges.append(exchange)
    pp.pprint(exchange)

# Load and update state
print 'Updating and writing state..'
with open('mockserver/public/v3/state', 'r') as f:
    obj = json.load(f)['data']
    obj['countries'][zone_name] = {}
    # Update production
    obj['countries'][zone_name] = production
    production['datetime'] = arrow.get(production['datetime']).isoformat()
    # Set random co2 value
    production['co2intensity'] = random() * 500
    # Update exchanges
    for e in exchanges:
        exchange_zone_names = e['sortedCountryCodes'].split('->')
        e['datetime'] = arrow.get(e['datetime']).isoformat()
        obj['exchanges'][e['sortedCountryCodes']] = e.copy()

        export_origin_zone_name = exchange_zone_names[0] if e['netFlow'] >= 0 else exchange_zone_names[1]
        obj['exchanges'][e['sortedCountryCodes']]['co2intensity'] = \
            obj['countries'].get(export_origin_zone_name, {}).get('co2intensity')

        for z in exchange_zone_names:
            other_zone = exchange_zone_names[(exchange_zone_names.index(z) + 1) % 2]
            if not z in obj['countries']:
                obj['countries'][z] = {}
            if not 'exchange' in obj['countries'][z]:
                obj['countries'][z]['exchange'] = {}
            if not 'exchangeCo2Intensities' in obj['countries'][z]:
                obj['countries'][z]['exchangeCo2Intensities'] = {}
            obj['countries'][z]['exchange'][other_zone] = e['netFlow']
            if z == exchange_zone_names[0]:
                obj['countries'][z]['exchange'][other_zone] *= -1

            # Use this zone's carbon intensity if it's an export, or if exchange is missing
            is_import = other_zone == export_origin_zone_name
            obj['countries'][z]['exchangeCo2Intensities'][other_zone] = \
                obj['countries'].get(other_zone, {}).get('co2intensity',
                    obj['countries'][z].get('co2intensity', None)) if is_import \
                else obj['countries'][z].get('co2intensity', None)
            
    # Set state datetime
    obj['datetime'] = production['datetime']
    # Save
with open('mockserver/public/v3/state', 'w') as f:
    json.dump({'data': obj}, f)
print '..done'
