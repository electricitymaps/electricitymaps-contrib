#!/usr/bin/env python3

"""
Script to manually update the state of the electricity map mockserver.

To use run the following command from the root directory.

PYTHONPATH=. python3 mockserver/update_state.py <zone_name>

Args:
<zone_name> - required zone in ISO 3166-1 format, pass <all> for every zone.

Any errors raised by parsers will be printed to the commandline in full, but
will not stop the following execution of other parsers.
"""


import arrow
import importlib
import json
import pprint
from random import random
import sys
import traceback


pp = pprint.PrettyPrinter(indent=2)

# Read parser import list from config jsons
with open('config/zones.json') as zc:
    zones_config = json.load(zc)
with open('config/exchanges.json') as ec:
    exchanges_config = json.load(ec)

# Read zone_name from commandline
if not len(sys.argv) > 1:
    raise Exception('Missing argument <zone_name>')

if sys.argv[1] == 'all':
    zone_names = list(zones_config.keys())
    zone_config = zones_config
else:
    zone_names = [sys.argv[1]]
    zone_config = zones_config

exchange_parser_keys = set()
for k in exchanges_config.keys():
    if sys.argv[1] == 'all':
        exchange_parser_keys = list(exchanges_config.keys())
        break
    zones = k.split('->')
    for zone_name in zone_names:
        if zone_name in zones:
            exchange_parser_keys.add(k)

# Import / run production parser
production_datapoints = []
for k in zone_names:
    try:
        production_parser = zone_config[k]['parsers']['production']
    except KeyError as e:
        # There is no production parser for this zone.
        print('No production parser found for {}'.format(k))
        continue

    mod_name, fun_name = production_parser.split('.')

    print('Finding and executing %s production parser %s..' % (k,
                                                              production_parser))

    try:
        mod = importlib.import_module('parsers.%s' % mod_name)
        production = getattr(mod, fun_name)(k)
        if type(production) == list:
            production = production[-1]
        if production is not None:
            production_datapoints.append(production)
        pp.pprint(production)
    except Exception as e:
        traceback.print_exc()

# Import / run exchange parser(s)
exchanges = []
for k in exchange_parser_keys:
    try:
        exchange_parser = exchanges_config[k]['parsers']['exchange']
    except KeyError as e:
        # There is no exchange implemented yet.
        print('No exchange parser found for {}'.format(k))
        continue

    mod_name, fun_name = exchange_parser.split('.')

    try:
        mod = importlib.import_module('parsers.%s' % mod_name)
        sorted_zone_names = sorted(k.split('->'))
        exchange = getattr(mod, fun_name)(sorted_zone_names[0], sorted_zone_names[1])
        if type(exchange) == list:
            exchange = exchange[-1]
        exchanges.append(exchange)
        pp.pprint(exchange)
    except Exception as e:
        traceback.print_exc()

# Load and update state
print('Updating and writing state..')
with open('mockserver/public/v3/state', 'r') as f:
    obj = json.load(f)['data']
    for dp in production_datapoints:
        production = dict(dp)
        obj['countries'][dp['zoneKey']] = production
        # Update production
        production['datetime'] = arrow.get(production['datetime']).isoformat()
        # Set random co2 value
        production['co2intensity'] = random() * 800
        # Set aggregates
        production['maxProduction'] = max([x or 0 for x in production['production'].values()])
        production['totalProduction'] = sum([x or 0 for x in production['production'].values()])

    # Update exchanges
    for e in exchanges:
        exchange_zone_names = e['sortedZoneKeys'].split('->')
        e['datetime'] = arrow.get(e['datetime']).isoformat()
        obj['exchanges'][e['sortedZoneKeys']] = e.copy()

        export_origin_zone_name = exchange_zone_names[0] if e['netFlow'] >= 0 else exchange_zone_names[1]
        obj['exchanges'][e['sortedZoneKeys']]['co2intensity'] = \
            obj['countries'].get(export_origin_zone_name, {}).get('co2intensity')

        for z in exchange_zone_names:
            other_zone = exchange_zone_names[(exchange_zone_names.index(z) + 1) % 2]
            if z not in obj['countries']:
                obj['countries'][z] = {}
            if 'exchange' not in obj['countries'][z]:
                obj['countries'][z]['exchange'] = {}
            if 'exchangeCo2Intensities' not in obj['countries'][z]:
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
    obj['datetime'] = arrow.now('Europe/Amsterdam').isoformat()

# Save
with open('mockserver/public/v3/state', 'w') as f:
    json.dump({'data': obj}, f)
print('..done')
