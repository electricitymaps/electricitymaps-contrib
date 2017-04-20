# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import pandas as pd

AMEO_CATEGORY_DICTIONARY = {
    'Bagasse': 'biomass',
    'Black Coal': 'coal',
    'Brown Coal': 'coal',
    'coal': 'coal',
    'Coal Seam Methane': 'gas',
    'Diesel': 'oil',
    'gas': 'gas',
    'Macadamia Nut Shells': 'biomass',
    'hydro': 'hydro',
    'Kerosene': 'oil',
    'Landfill / Biogass': 'biomass',
    'Landfill Gas': 'biomass',
    'Landfill Methane / Landfill Gas': 'biomass',
    'Landfill, Biogas': 'biomass',
    'Macadamia Nut Shells': 'biomass',
    'Natural Gas': 'gas',
    'Natural Gas / Diesel': 'gas',
    'Natural Gas / Fuel Oil': 'gas',
    'oil': 'oil',
    'Sewerage/Waste Water': 'biomass',
    'Solar': 'solar',
    'Solar PV': 'solar',
    'Waste Coal Mine Gas': 'gas',
    'Waste Water / Sewerage': 'biomass',
    'Water': 'hydro',
    'Wind': 'wind'
}

AMEO_STATION_DICTIONARY = {
    'Basslink HVDC Link': 'Import / Export',
    # 'Bendeela / Kangaroo Valley Pumps': 'storage',
    # 'Rocky Point Cogeneration Plant': 'storage',
    # 'Wivenhoe Power Station No. 1 Pump': 'storage',
    # 'Wivenhoe Power Station No. 2 Pump': 'storage',
    'Yarwun Power Station': 'coal'
}


def fetch_production(country_code='AU', session=None):
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
    url = 'http://services.aremi.nationalmap.gov.au/aemo/v3/csv/all'
    df = pd.read_csv(url)
    data = {
        'countryCode': country_code,
        'capacity': {},
        'production': {},
        'storage': {},
        'source': 'aremi.nationalmap.gov.au',
    }
    for rowIndex, row in df.iterrows():
        if row['Most Recent Output Time (AEST)'] == '-': continue
        fuelsource = row['Fuel Source - Descriptor']
        station = row['Station Name']
        if not fuelsource in AMEO_CATEGORY_DICTIONARY and not station in AMEO_STATION_DICTIONARY:
            # Only show warning if it actually produces something
            if float(row['Current Output (MW)']) if row['Current Output (MW)'] != '-' else 0.0:
                print 'WARNING: key %s is not supported' % fuelsource
                print row
            continue

        # Skip HVDC links
        if AMEO_CATEGORY_DICTIONARY.get(station, None) == 'Import / Export':
            continue

        key = AMEO_CATEGORY_DICTIONARY.get(fuelsource, None) or \
            AMEO_STATION_DICTIONARY.get(station)
        value = float(row['Current Output (MW)']) if row['Current Output (MW)'] != '-' else 0.0

        # Check for negativity, but not too much
        if value < -1:
            print 'Skipping because production can\'t be negative (%s)' % value
            print row
            continue
        
        if not key in data['production']: data['production'][key] = 0.0
        if not key in data['capacity']: data['capacity'][key] = 0.0
        data['production'][key] += value
        data['capacity'][key] += float(row['Max Cap (MW)'])
        data['production'][key] = max(data['production'][key], 0)
        data['capacity'][key] = max(data['capacity'][key], 0)
        
        # Parse the datetime and return a python datetime object
        datetime = arrow.get(row['Most Recent Output Time (AEST)']).datetime
        # TODO: We should check it's not too old..
        if not 'datetime' in data:
            data['datetime'] = datetime
        else:
            data['datetime'] = max(datetime, data['datetime'])

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
