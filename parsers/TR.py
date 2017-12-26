#!/usr/bin/env python3

import requests
import re
import json
import arrow

SEARCH_DATA = re.compile(r'var gunlukUretimEgrisiData = (?P<data>.*);')
TIMEZONE = 'Europe/Istanbul'
URL = 'https://ytbs.teias.gov.tr/ytbs/frm_login.jsf'
EMPTY_DAY = -1

MAP_GENERATION = {
    'akarsu': 'hydro',
    'barajli': 'hydro',
    'dogalgaz': 'gas',
    'jeotermal': 'geothermal',
    'taskomur': 'coal',
    'asfaltitkomur': 'coal',
    'linyit': 'coal',
    'ithalkomur': 'coal',
    'ruzgar': 'wind',
    'fueloil': 'oil',
    'biyokutle': 'biomass',
    'nafta': 'unknown'
}


def as_float(prod):
    """Convert json values to float and sum all production for a further use"""
    prod['total'] = 0.0
    if isinstance(prod, dict) and 'yuk' not in prod.keys():
        for prod_type, prod_val in prod.items():
            prod[prod_type] = float(prod_val)
            prod['total'] += prod[prod_type]
    return prod


def get_last_data_idx(productions):
    """
    Find index of the last production
    :param productions: list of 24 production dict objects
    :return: (int) index of the newest data or -1 if no data (empty day)
    """
    for i in range(len(productions)):
        if productions[i]['total'] < 1000:
            return i - 1
    return len(productions) - 1  # full day


def fetch_production(country_code='TR', session=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'countryCode': 'FR',
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
    session = None  # Explicitely make a new session to avoid caching from their server...
    r = session or requests.session()
    tr_datetime = arrow.now().to('Europe/Istanbul').floor('day')
    response = r.get(URL, verify=False)
    str_data = re.search(SEARCH_DATA, response.text)

    production_by_hour = []
    if str_data:
        productions = json.loads(str_data.group('data'), object_hook=as_float)
        last_data_index = get_last_data_idx(productions)
        valid_production = productions[:last_data_index + 1]
        if last_data_index != EMPTY_DAY:
            for datapoint in valid_production:
                data = {
                  'countryCode': country_code,
                  'production': {},
                  'storage': {},
                  'source': 'ytbs.teias.gov.tr',
                  'datetime': None
                }
                data['production'] = dict(zip(MAP_GENERATION.values(), [0] * len(MAP_GENERATION)))
                for prod_type, prod_val in datapoint.items():
                    if prod_type in MAP_GENERATION.keys():
                        data['production'][MAP_GENERATION[prod_type]] += prod_val

                try:
                    data['datetime'] = tr_datetime.replace(hour=int(datapoint['saat'])).datetime
                except ValueError:
                    # 24 is not a valid hour!
                    data['datetime'] = tr_datetime.datetime

                production_by_hour.append(data)
    else:
        raise Exception('Extracted data was None')

    return production_by_hour


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
