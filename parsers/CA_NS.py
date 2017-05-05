# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import re


def _get_ns_info(requests_obj):
    country_code = 'CA-NS'

    mix_url = 'http://www.nspower.ca/system_report/today/currentmix.json'
    mix_data = requests_obj.get(mix_url).json()

    load_url = 'http://www.nspower.ca/system_report/today/currentload.json'
    load_data = requests_obj.get(load_url).json()

    production = []
    imports = []
    for mix in mix_data:
        corresponding_load = [load_period for load_period in load_data
                              if load_period['datetime'] == mix['datetime']]

        # in mix_data, the values are expressed as percentages,
        # e.g. "Solid Fuel":  45.76 meaning 45.76%
        # Divide load by 100.0 to simplify calculations later on.
        if corresponding_load:
            load = corresponding_load[0]['Base Load'] / 100.0
        else:
            # if not found, assume 1244 MW, based on average yearly electricity available for use
            # in 2014 and 2015 (Statistics Canada table Table 127-0008 for Nova Scotia)
            load = 1244 / 100.0

        # datetime is in format '/Date(1493924400000)/'
        # get the timestamp 1493924400 (cutting out last three zeros as well)
        data_timestamp = int(mix['datetime'][6:-5])
        data_date = arrow.get(data_timestamp).datetime

        production.append({
            'countryCode': country_code,
            'datetime': data_date,
            'production': {
                'coal': (mix['Solid Fuel'] * load),
                'gas': ((mix['HFO/Natural Gas'] + mix['CT\'s'] + mix['LM 6000\'s']) * load),
                'biomass': (mix['Biomass'] * load),
                'hydro': (mix['Hydro'] * load),
                'wind': (mix['Wind'] * load)
            },
            'source': 'nspower.ca',
        })

        # In this source, imports are positive. In the expected result for CA-NB->CA-NS,
        # "net" represents a flow from NB to NS, that is, an import to NS.
        # So the value can be used directly.
        # Note that this API only specifies imports. When NS is exporting energy, the API returns 0.
        imports.append({
            'datetime': data_date,
            'netFlow': (mix['Imports'] * load),
            'source': 'nspower.ca'
        })

    return production, imports


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

    production, imports = _get_ns_info(r)

    return production


def fetch_exchange(country_code1, country_code2, session=None):
    """Requests the last known power exchange (in MW) between two regions.

    Note: As of early 2017, Nova Scotia only has an exchange with New Brunswick (CA-NB).
    (An exchange with Newfoundland, "Maritime Link", is scheduled to open in "late 2017").

    The API for Nova Scotia only specifies imports. When NS is exporting energy,
    the API returns 0.
    """
    sorted_country_codes = '->'.join(sorted([country_code1, country_code2]))

    if sorted_country_codes != 'CA-NB->CA-NS':
        raise NotImplementedError('This exchange pair is not implemented')

    requests_obj = session or requests.session()
    _, imports = _get_ns_info(requests_obj)

    data = imports[-1]
    data['sortedCountryCodes'] = sorted_country_codes

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())

    print('fetch_exchange("CA-NS", "CA-NB") ->')
    print(fetch_exchange("CA-NS", "CA-NB"))
