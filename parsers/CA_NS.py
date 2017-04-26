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
    mix_url = 'http://www.nspower.ca/system_report/today/currentmix.json'
    mix_data = r.get(mix_url).json()

    load_url = 'http://www.nspower.ca/system_report/today/currentload.json'
    load_data = r.get(load_url).json()

    data = []
    for mix in mix_data:
        corresponding_load = [load_period for load_period in load_data
                              if load_period['datetime'] == mix['datetime']]

        # in mix_data, the values are expressed as percentages,
        # e.g. "Solid Fuel":  45.76 meaning 45.76%
        # Divide load by 100.0 to simplify calculations later on.
        if corresponding_load:
            load = corresponding_load[0]['Base Load'] / 100.0
        else:
            # if not found, assume 1500 MW, based on total available capacity of around 2500 MW
            load = 1500 / 100.0

        data.append({
            'countryCode': country_code,
            'datetime': arrow.get(
                int(re.search('\d+', mix['datetime']).group(0)) / 1000.0).datetime,
            'production': {
                'coal': (mix['Solid Fuel'] * load),
                'gas': ((mix['HFO/Natural Gas'] + mix['CT\'s'] + mix['LM 6000\'s']) * load),
                'biomass': (mix['Biomass'] * load),
                'hydro': (mix['Hydro'] * load),
                'wind': (mix['Wind'] * load),
                'unknown': (mix['Imports'] * load)
            },
            'storage': {},
            'source': 'nspower.ca',
        })

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
