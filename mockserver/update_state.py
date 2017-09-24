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
        zones = e['sortedCountryCodes'].split('->')
        e['datetime'] = arrow.get(e['datetime']).isoformat()
        obj['exchanges'][e['sortedCountryCodes']] = e.copy()
        origin_zone = zones[0] if e['netFlow'] >= 0 else zones[1]
        obj['exchanges'][e['sortedCountryCodes']]['co2intensity'] = \
            obj['countries'].get(origin_zone, {}).get('co2intensity')
        for z in zones:
            other_zone = zones[(zones.index(z) + 1) % 2]
            if not z in obj['countries']:
                obj['countries'][z] = {}
            if not 'exchange' in obj['countries'][z]:
                obj['countries'][z]['exchange'] = {}
            obj['countries'][z]['exchange'][other_zone] = e['netFlow']
            print z, other_zone
            if z == zones[0]:
                obj['countries'][z]['exchange'][other_zone] *= -1
            
    # Set state datetime
    obj['datetime'] = production['datetime']
    # Save
with open('mockserver/public/v3/state', 'w') as f:
    json.dump({'data': obj}, f)
print '..done'
