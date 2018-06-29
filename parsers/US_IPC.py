#!usr/bin/env python3

"""Parser for the Idaho Power Comapny area of the United States."""

from dateutil import parser, tz
from itertools import groupby
from logging import getLogger
import requests


# NOTE No pumped storage yet but future ideas can be found at the following url.
# https://docs.idahopower.com/pdfs/AboutUs/PlanningForFuture/irp/IRP.pdf

# Renewable energy (PURPA) is likely bought with credits from outside the Utility
# area and not supplied to customers. For that reason those types are commented out.

PRODUCTION_URL = 'https://api.idahopower.com/Energy/Api/V1/GenerationAndDemand/Subset'

GENERATION_MAPPING = {'Non-Utility Geothermal': 'geothermal',
                      'Hydro': 'hydro',
                      'Coal': 'coal',
                      'Diesel': 'oil',
                      'PURPA/Non-Utility Wind': 'wind',
                      'Natural Gas': 'gas',
                      'PURPA/Non-Utility Solar': 'solar'
                      #'PURPA Other': 'biomass'
                      }

TIMEZONE = tz.gettz("America/Boise")


def get_data(session=None):
    """Returns a list of dictionaries."""

    s = session or requests.Session()

    req = requests.get(PRODUCTION_URL)
    json_data = req.json()
    raw_data = json_data['list']

    return raw_data


def timestamp_converter(timestamp):
    """Converts a str timestamp into an aware datetime object."""

    dt_naive = parser.parse(timestamp)
    dt_aware = dt_naive.replace(tzinfo=TIMEZONE)

    return dt_aware


def data_processer(raw_data, logger):
    """
    Groups dictionaries by datetime key.
    Removes unneeded keys and logs any new ones.
    Returns a list of tuples containing (datetime object, dictionary).
    """

    dt_key = lambda x: x['datetime']
    grouped = groupby(raw_data, dt_key)

    keys_to_ignore = {'Load', 'Net Purchases', 'Inadvertent', 'PURPA Other'}
    known_keys = GENERATION_MAPPING.keys() | keys_to_ignore

    unmapped = set()
    parsed_data = []
    for group in grouped:
        dt = timestamp_converter(group[0])
        generation = group[1]

        production = {}
        for gen_type in generation:
            production[gen_type['name']] = float(gen_type['data'])

        current_keys = production.keys() | set()
        unknown_keys = current_keys - known_keys
        unmapped = unmapped | unknown_keys

        keys_to_remove = keys_to_ignore | unknown_keys

        for key in keys_to_remove:
            production.pop(key, None)

        production = {GENERATION_MAPPING[k]: v for k, v in production.items()}

        parsed_data.append((dt, production))

    for key in unmapped:
        logger.warning('Key \'{}\' in US-IPC is not mapped to type.'.format(key), extra={'key': 'US-IPC'})

    return parsed_data


def fetch_production(zone_key = 'US-IPC', session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_data = get_data(session=session)
    processed_data = data_processer(raw_data, logger)

    production_data = []
    for item in processed_data:
        datapoint = {
          'zoneKey': zone_key,
          'datetime': item[0],
          'production': item[1],
          'storage': {},
          'source': 'idahopower.com'
        }

        production_data.append(datapoint)

    return production_data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
