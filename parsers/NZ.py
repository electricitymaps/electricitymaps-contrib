# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import json
from bs4 import BeautifulSoup

timezone = 'Pacific/Auckland'

def fetch(session=None):
    r = session or requests.session()
    url = 'https://www.transpower.co.nz/power-system-live-data'
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for item in soup.find_all('script'):
        if 'src' in item.attrs: continue
        body = item.contents[0]
        if not body.startswith('jQuery.extend(Drupal.settings'):
            continue
        obj = json.loads(body.replace('jQuery.extend(Drupal.settings, ', '').replace(');', ''))
        break
    return obj


def fetch_production(country_code=None, session=None):
    """Requests the last known production mix (in MW) of a given country

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
    obj = fetch(session)

    datetime = arrow.get(obj['soPgenGraph']['timestamp']).datetime

    if country_code == 'NZ-NZN':
        region_key = 'North Island'
    elif country_code == 'NZ-NZS':
        region_key = 'South Island'
    else:
        raise NotImplementedError('Unsupported country_code %s' % country_code)

    productions = obj['soPgenGraph']['data'][region_key]

    data = {
        'countryCode': country_code,
        'datetime': datetime,
        'production': {
            'coal': productions.get('Gas/Coal', {'generation': 0.0})['generation'],
            'oil': productions.get('Diesel/Oil', {'generation': 0.0})['generation'],
            'gas': productions.get('Gas', {'generation': 0.0})['generation'],
            'geothermal': productions.get('Geothermal', {'generation': 0.0})['generation'],
            'wind': productions.get('Wind', {'generation': 0.0})['generation'],
            'hydro': productions.get('Hydro', {'generation': 0.0})['generation'],
            'unknown': productions.get('Co-Gen', {'generation': 0.0})['generation']
        },
        'capacity': {
            'coal': productions.get('Gas/Coal', {'capacity': 0.0})['capacity'],
            'oil': productions.get('Diesel/Oil', {'capacity': 0.0})['capacity'],
            'gas': productions.get('Gas', {'capacity': 0.0})['capacity'],
            'geothermal': productions.get('Geothermal', {'capacity': 0.0})['capacity'],
            'wind': productions.get('Wind', {'capacity': 0.0})['capacity'],
            'hydro': productions.get('Hydro', {'capacity': 0.0})['capacity'],
            'unknown': productions.get('Co-Gen', {'capacity': 0.0})['capacity']
        },
        'storage': {},
        'source': 'transpower.co.nz',
    }

    return data


def fetch_exchange(country_code1='NZ-NZN', country_code2='NZ-NZS', session=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """

    obj = fetch(session)['soHVDCDailyGraph']
    datetime_start = arrow.get(arrow.now().datetime, 'Pacific/Auckland').floor('day')
    data = []
    for item in obj['data']['mw_north']:
        datetime = datetime_start.replace(minutes=+item[0])
        if datetime > arrow.get() or item[1] is None:
            continue
        netFlow = item[1]
        data.append({
              'sortedCountryCodes': 'NZ-NZN->NZ-NZS',
              'datetime': datetime.datetime,
              'netFlow': -1 * netFlow,
              'source': 'transpower.co.nz'
          })

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production(NZ-NZN) ->'
    print fetch_production('NZ-NZN')
    print 'fetch_production(NZ-NZS) ->'
    print fetch_production('NZ-NZS')
    print 'fetch_exchange() ->'
    print fetch_exchange()
