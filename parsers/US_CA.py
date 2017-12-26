#!/usr/bin/env python3
# The arrow library is used to handle datetimes
import arrow
# The pandas library is used to parse content through HTTP
import pandas

def fetch_production(country_code='US-CA', session=None):
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
    # Get the production from the CSV
    csv_url = 'http://www.caiso.com/outlook/SP/fuelsource.csv'
    csv = pandas.read_csv(csv_url)
    latest_index = len(csv)-1
    production_map = {
        'Solar': 'solar',
        'Wind': 'wind',
        'Geothermal': 'geothermal',
        'Biomass': 'biomass',
        'Biogas': 'biomass',
        'Small hydro': 'hydro',
        'Coal': 'coal',
        'Nuclear': 'nuclear',
        'Natural gas': 'gas',
        'Large hydro': 'hydro',
        'Other': 'unknown'
    }
    storage_map = {
        'Batteries': 'battery'
    }
    dailyData = []
    for i in range(0, latest_index + 1):
        h, m = map(int, csv['Time'][i].split(':'))
        date = arrow.utcnow().to('US/Pacific').replace(hour = h, minute = m, second = 0, microsecond = 0)
        data = {
            'countryCode': country_code,
            'production': {},
            'storage': {},
            'source': 'caiso.com',
            'datetime': date.datetime
        }
        for key, value in production_map.items():
            prod = float(csv[key][i])
            # if another mean of production created a value, sum them up
            if value in data['production']:
                data['production'][value] += prod
            else:
                data['production'][value] = prod
        for key, value in storage_map.items():
            storage = -float(csv[key][i])
            # if another mean of storage created a value, sum them up
            if value in data['production']:
                data['storage'][value] += storage
            else:
                data['storage'][value] = storage
        dailyData.append(data)

    return dailyData


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
