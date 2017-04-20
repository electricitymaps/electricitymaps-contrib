# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import re


def fetch_production(country_code='CA-NS', session=None):
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
    r = session or requests.session()
    url = 'http://www.nspower.ca/system_report/today/currentmix.json'
    response = r.get(url)
    data = []
    for obj in response.json():
        data.append({
            'countryCode': country_code,
            'datetime': arrow.get(
                int(re.search('\d+', obj['datetime']).group(0)) / 1000.0).datetime,
            'production': {
                'coal': obj['Solid Fuel'],
                'gas': obj['HFO/Natural Gas'] + obj['CT\'s'] + obj['LM 6000\'s'],
                'biomass': obj['Biomass'],
                'hydro': obj['Hydro'],
                'wind': obj['Wind'],
                'unknown': obj['Imports']
            },
            'storage': {},
            'source': 'nspower.ca',
        })

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
