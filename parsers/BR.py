#!/usr/bin/env python3

from collections import defaultdict

import arrow
import requests

from .lib.validation import validate


url = 'http://tr.ons.org.br/Content/GetBalancoEnergetico/null'

generation_mapping = {
                      u'nuclear': 'nuclear',
                      u'eolica': 'wind',
                      u'termica': 'unknown',
                      u'solar': 'solar',
                      'hydro': 'hydro'
                      }

regions = {
           'BR-NE': u'nordeste',
           'BR-N': u'norte',
           'BR-CS': u'sudesteECentroOeste',
           'BR-S': u'sul'
           }

region_exchanges = {
                    'BR-CS->BR-S': "sul_sudeste",
                    'BR-CS->BR-NE': "sudeste_nordeste",
                    'BR-CS->BR-N': "sudeste_norteFic",
                    'BR-N->BR-NE': "norteFic_nordeste"
                    }


region_exchanges_directions = {
                    'BR-CS->BR-S': -1,
                    'BR-CS->BR-NE': 1,
                    'BR-CS->BR-N': 1,
                    'BR-N->BR-NE': 1
                    }

countries_exchange = {
    'UY': {
        'name': u'uruguai',
        'flow': 1
    },
    'AR': {
        'name': u'argentina',
        'flow': -1
    },
    'PY': {
        'name': u'paraguai',
        'flow': -1
    }
}


def get_data(session, logger):
    """Requests generation data in json format."""

    s = session or requests.session()
    json_data = s.get(url).json()
    return json_data


def production_processor(json_data, zone_key):
    """
    Extracts data timestamp and sums regional data into totals by key.
    Maps keys to type and returns a tuple.
    """

    dt = arrow.get(json_data['Data'])
    totals = defaultdict(lambda: 0.0)

    region = regions[zone_key]
    breakdown = json_data[region][u'geracao']
    for generation, val in breakdown.items():
        totals[generation] += val

    # BR_CS contains the Itaipu Dam.
    # We merge the hydro keys into one, then remove unnecessary keys.
    totals['hydro'] = totals.get(u'hidraulica', 0.0) + totals.get(u'itaipu50HzBrasil', 0.0) + totals.get(u'itaipu60Hz', 0.0)
    entriesToRemove = (u'hidraulica', u'itaipu50HzBrasil', u'itaipu60Hz', u'total')
    for k in entriesToRemove:
        totals.pop(k, None)

    mapped_totals = {generation_mapping.get(name, 'unknown'): val for name, val
                     in totals.items()}

    return dt, mapped_totals


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    gd = get_data(session, logger)
    generation = production_processor(gd, zone_key)

    datapoint = {
      'zoneKey': zone_key,
      'datetime': generation[0].datetime,
      'production': generation[1],
      'storage': {
          'hydro': None,
      },
      'source': 'ons.org.br'
    }

    datapoint = validate(datapoint, logger,
                         remove_negative=True, required=['hydro'], floor=1000)

    return datapoint


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two regions
    Arguments:
    zone_key1           -- the first country code
    zone_key2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    gd = get_data(session, logger)

    if zone_key1 in countries_exchange.keys():
        country_exchange = countries_exchange[zone_key1]

    if zone_key2 in countries_exchange.keys():
        country_exchange = countries_exchange[zone_key2]

    data = {
        'datetime': arrow.get(gd['Data']).datetime,
        'sortedZoneKeys': '->'.join(sorted([zone_key1, zone_key2])),
        'netFlow': gd['internacional'][country_exchange['name']] * country_exchange['flow'],
        'source': 'ons.org.br'
    }

    return data


def fetch_region_exchange(region1, region2, session=None, target_datetime=None, logger=None):
    """
    Requests the last known power exchange (in MW) between two Brazilian regions.
    Arguments:
    region1           -- the first region
    region2           -- the second region; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    gd = get_data(session, logger)
    dt = arrow.get(gd['Data']).datetime
    scc = '->'.join(sorted([region1, region2]))

    exchange = region_exchanges[scc]
    nf = gd['intercambio'][exchange] * region_exchanges_directions[scc]

    data = {
        'datetime': dt,
        'sortedZoneKeys': scc,
        'netFlow': nf,
        'source': 'ons.org.br'
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production(BR-NE) ->')
    print(fetch_production('BR-NE'))

    print('fetch_production(BR-N) ->')
    print(fetch_production('BR-N'))

    print('fetch_production(BR-CS) ->')
    print(fetch_production('BR-CS'))

    print('fetch_production(BR-S) ->')
    print(fetch_production('BR-S'))

    print('fetch_exchange(BR-S, UY) ->')
    print(fetch_exchange('BR-S', 'UY'))

    print('fetch_exchange(BR-S, AR) ->')
    print(fetch_exchange('BR-S', 'AR'))

    print('fetch_region_exchange(BR-CS->BR-S)')
    print(fetch_region_exchange('BR-CS', 'BR-S'))

    print('fetch_region_exchange(BR-CS->BR-NE)')
    print(fetch_region_exchange('BR-CS', 'BR-NE'))

    print('fetch_region_exchange(BR-CS->BR-N)')
    print(fetch_region_exchange('BR-CS', 'BR-N'))

    print('fetch_region_exchange(BR-N->BR-NE)')
    print(fetch_region_exchange('BR-N', 'BR-NE'))
