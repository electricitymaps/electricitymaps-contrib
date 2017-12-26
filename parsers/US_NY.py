#!/usr/bin/env python3

"""Real time parser for the state of New York."""
import arrow
from collections import defaultdict
from operator import itemgetter
import pandas as pd

mapping = {
           'Dual Fuel': 'unknown',
           'Natural Gas': 'gas',
           'Nuclear': 'nuclear',
           'Other Fossil Fuels': 'unknown',
           'Other Renewables': 'unknown',
           'Wind': 'wind',
           'Hydro': 'hydro'
           }

def read_csv_data(url):
    """
    Gets csv data from a url and returns a dataframe.
    """

    csv_data = pd.read_csv(url)

    return csv_data

def timestamp_converter(timestamp_string):
    """
    Converts timestamps in nyiso data into aware datetime objects.
    """

    dt_naive = arrow.get(timestamp_string, 'MM/DD/YYYY HH:mm:ss')
    dt_aware = dt_naive.replace(tzinfo = 'America/New_York').datetime

    return dt_aware

def data_parser(df):
    """
    Takes dataframe and loops over rows to form dictionaries consisting of datetime and generation type.
    Merges these dictionaries using datetime key.
    Maps to type and returns a list of tuples containing datetime string and production.
    """

    chunks = []
    for row in df.itertuples():
        piece = {}
        piece['datetime'] = row[1]
        piece[row[3]] = row[4]
        chunks.append(piece)

    #Join dicts on shared 'datetime' keys.
    combine = defaultdict(dict)
    for elem in chunks:
        combine[elem['datetime']].update(elem)

    ordered = sorted(combine.values(), key = itemgetter("datetime"))

    mapped_generation = []
    for item in ordered:
        mapped_types = [(mapping.get(k, k), v) for k, v in item.items()]

        #Need to avoid multiple 'unknown' keys overwriting.
        complete_production = defaultdict(lambda: 0.0)
        for key,val in mapped_types:
            try:
                complete_production[key] += val
            except TypeError:
                #Datetime is a string at this point!
                complete_production[key] = val

        dt = complete_production.pop('datetime')
        final = (dt, dict(complete_production))
        mapped_generation.append(final)

    return mapped_generation

def fetch_production(country_code = 'US-NY', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
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

    ny = arrow.now('America/New_York')
    ny_date = ny.format('YYYYMMDD')
    mix_url = 'http://mis.nyiso.com/public/csv/rtfuelmix/{}rtfuelmix.csv'.format(ny_date)
    raw_data = read_csv_data(mix_url)
    clean_data = data_parser(raw_data)

    production_mix = []
    for datapoint in clean_data:
        data = {
          'countryCode': country_code,
          'datetime': timestamp_converter(datapoint[0]),
          'production': datapoint[1],
          'storage': {'hydro': None},
          'source': 'nyiso.com'
        }

        production_mix.append(data)

    return production_mix

def fetch_exchange(country_code1, country_code2, session=None):
    """Requests the last known power exchange (in MW) between two zones
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

    ny = arrow.now('America/New_York')
    ny_date = ny.format('YYYYMMDD')
    exchange_url = 'http://mis.nyiso.com/public/csv/ExternalLimitsFlows/{}ExternalLimitsFlows.csv'.format(ny_date)
    exchange_data = read_csv_data(exchange_url)

    relevant_exchanges = ['SCH - NE - NY', 'SCH - NPX_1385', 'SCH - NPX_CSC']
    new_england_exs = exchange_data.loc[exchange_data['Interface Name'].isin(relevant_exchanges)]
    consolidated_flows = new_england_exs.reset_index().groupby("Timestamp").sum()

    sortedcodes = '->'.join(sorted([country_code1,country_code2]))

    exchange_5min = []
    for row in consolidated_flows.itertuples():
        flow = float(row[3])
        #Timestamp for exchange does not include seconds.
        dt = timestamp_converter(row[0] + ':00')

        exchange = {
          'sortedCountryCodes': sortedcodes,
          'datetime': dt,
          'netFlow': flow,
          'source': 'nyiso.com'
        }

        exchange_5min.append(exchange)

    return exchange_5min


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(US-NY, US-NEISO)')
    print(fetch_exchange('US-NY', 'US-NEISO'))
