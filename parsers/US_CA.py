#!/usr/bin/env python3

from collections import defaultdict

# The arrow library is used to handle datetimes
import arrow
# The pandas library is used to parse content through HTTP
import pandas

FUEL_SOURCE_CSV = 'http://www.caiso.com/outlook/SP/fuelsource.csv'


def fetch_production(zone_key='US-CA', session=None, target_datetime=None,
                     logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session

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
        return fetch_historical_production(target_datetime)

    target_datetime = arrow.get(target_datetime)

    # Get the production from the CSV
    csv = pandas.read_csv(FUEL_SOURCE_CSV)
    latest_index = len(csv) - 1
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
    daily_data = []
    for i in range(0, latest_index + 1):
        h, m = map(int, csv['Time'][i].split(':'))
        date = arrow.utcnow().to('US/Pacific').replace(hour=h, minute=m,
                                                       second=0, microsecond=0)
        data = {
            'zoneKey': zone_key,
            'production': defaultdict(float),
            'storage': defaultdict(float),
            'source': 'caiso.com',
            'datetime': date.datetime
        }

        # map items from names in CAISO CSV to names used in Electricity Map
        for ca_gen_type, mapped_gen_type in production_map.items():
            production = float(csv[ca_gen_type][i])

            # if another mean of production created a value, sum them up
            data['production'][mapped_gen_type] += production

        for ca_storage_type, mapped_storage_type in storage_map.items():
            storage = -float(csv[ca_storage_type][i])

            # if another mean of storage created a value, sum them up
            data['storage'][mapped_storage_type] += storage

        daily_data.append(data)

    return daily_data


def fetch_historical_production(target_datetime):
    return fetch_historical_data(target_datetime)[0]


def fetch_historical_exchange(target_datetime):
    return fetch_historical_data(target_datetime)[1]


def fetch_historical_data(target_datetime):
    # caiso.com provides daily data until the day before today
    # get a clean date at the beginning of yesterday
    target_date = arrow.get(target_datetime).to('US/Pacific').replace(
        hour=0, minute=0, second=0, microsecond=0)

    url = 'http://content.caiso.com/green/renewrpt/' + target_date.format(
        'YYYYMMDD') + '_DailyRenewablesWatch.txt'

    renewable_resources = pandas.read_table(
        url, sep='\t\t', skiprows=2, header=None,
        names=['Hour', 'GEOTHERMAL', 'BIOMASS', 'BIOGAS', 'SMALL HYDRO',
               'WIND TOTAL', 'SOLAR PV', 'SOLAR THERMAL'],
        skipfooter=27, skipinitialspace=True, engine='python')
    other_resources = pandas.read_table(
        url, sep='\t\t', skiprows=30, header=None,
        names=['Hour', 'RENEWABLES', 'NUCLEAR', 'THERMAL', 'IMPORTS', 'HYDRO'],
        skipinitialspace=True, engine='python')

    daily_data, import_data = [], []

    for i in range(0, 24):
        daily_data.append({
            'zoneKey': 'US-CA',
            'storage': {},
            'source': 'caiso.com',
            'production': {
                'biomass': float(renewable_resources['BIOMASS'][i]),
                'gas': float(renewable_resources['BIOGAS'][i])
                       + float(other_resources['THERMAL'][i]),
                'hydro': float(renewable_resources['SMALL HYDRO'][i])
                         + float(other_resources['HYDRO'][i]),
                'nuclear': float(other_resources['NUCLEAR'][i]),
                'solar': float(renewable_resources['SOLAR PV'][i])
                         + float(renewable_resources['SOLAR THERMAL'][i]),
                'wind': float(renewable_resources['WIND TOTAL'][i]),
                'geothermal': float(renewable_resources['GEOTHERMAL'][i]),
            },
            'datetime': target_date.shift(hours=i + 1).datetime,
        })
        import_data.append(
            {
                'sortedZoneKeys': 'US-CA->US-intoCA',
                'datetime': target_date.shift(hours=i + 1).datetime,
                'netFlow': other_resources['IMPORTS'][i] * -1,
                'source': 'caiso.com'
            }
        )

    return daily_data, import_data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    zone_key1: the first country code
    zone_key2: the second country code; order of the two codes in params
      doesn't matter
    session: request session passed in order to re-use an existing session
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
    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))
    if sorted_zone_keys != 'US-CA->US-intoCA':
        raise NotImplementedError(
            'Exchange pair not supported: {}'.format(sorted_zone_keys))

    if target_datetime:
        return fetch_historical_exchange(target_datetime)

    # CSV has imports to California as positive.
    # Electricity Map expects A->B to indicate flow to B as positive.
    # So values in CSV can be used as-is.

    csv = pandas.read_csv(FUEL_SOURCE_CSV)
    latest_index = len(csv) - 1
    daily_data = []
    for i in range(0, latest_index + 1):
        h, m = map(int, csv['Time'][i].split(':'))
        date = arrow.utcnow().to('US/Pacific').replace(hour=h, minute=m,
                                                       second=0, microsecond=0)
        data = {
            'sortedZoneKeys': sorted_zone_keys,
            'datetime': date.datetime,
            'netFlow': csv['Imports'][i] * -1,
            'source': 'caiso.com'
        }

        daily_data.append(data)

    return daily_data


if __name__ == '__main__':
    "Main method, not used by Electricity Map backend, but handy for testing"

    from pprint import pprint

    print('fetch_production() ->')
    pprint(fetch_production())

    print('fetch_exchange("US-CA", "US-intoCA") ->')
    pprint(fetch_exchange("US-CA", "US-intoCA"))
