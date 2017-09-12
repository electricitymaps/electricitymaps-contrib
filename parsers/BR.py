#!/usr/bin/python

import arrow
from collections import defaultdict
import requests

url ='http://tr.ons.org.br/Content/GetBalancoEnergetico/null'

generation_mapping = {
                      u'nuclear': 'nuclear',
                      u'eolica': 'wind',
                      u'termica': 'unknown',
                      u'solar': 'solar',
                      'hydro' : 'hydro'
                      }

regions = [u'nordeste', u'norte', u'sudesteECentroOeste', u'sul']


def get_data(session = None):
    """Requests generation data in json format."""

    s = session or requests.session()
    json_data = s.get(url).json()

    return json_data


def production_processor(json_data):
    """
    Extracts data timestamp and sums regional data into totals by key.
    Maps keys to type and returns a tuple.
    """

    dt = arrow.get(json_data['Data'])
    totals = defaultdict(lambda: 0.0)

    for region in regions:
        breakdown = json_data[region][u'geracao']
        for generation, val in breakdown.items():
            totals[generation] += val

    #We merge the 3 hydro keys into one, then remove unnecessary keys.
    totals['hydro'] = totals[u'hidraulica'] + totals[u'itaipu50HzBrasil'] + totals[u'itaipu60Hz']
    entriesToRemove = (u'hidraulica', u'itaipu50HzBrasil', u'itaipu60Hz', u'total')
    for k in entriesToRemove:
        totals.pop(k, None)

    mapped_totals = {generation_mapping.get(name, 'unknown'): val for name, val in totals.items()}

    return dt, mapped_totals


def fetch_production(country_code = 'BR', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
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

    gd = get_data()
    generation = production_processor(gd)

    datapoint = {
      'countryCode': country_code,
      'datetime': generation[0].datetime,
      'production': generation[1],
      'storage': {
          'hydro': None,
      },
      'source': 'ons.org.br'
    }

    return datapoint

def fetch_exchange(country_code1='BR', country_code2='UY', session=None):
    """Requests the last known power exchange (in MW) between two regions
    Arguments:
    country_code1           -- the first country code
    country_code2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    gd = get_data()

    data = {
        'datetime': gd['Data'],
        'sortedCountryCodes': 'BR->UY',
        'netFlow': gd['internacional']['uruguai'],
        'source': 'ons.org.br'
    }

    return data

if __name__ ==  '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())

    print('fetch_exchange() ->')
    print(fetch_exchange())
