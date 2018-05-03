#!/usr/bin/env python3

"""Parser for the Bonneville Power Administration area of the USA."""

from datetime import datetime, timedelta
from io import StringIO
import logging
import pandas as pd
import pytz
import requests


GENERATION_URL = 'https://transmission.bpa.gov/business/operations/Wind/baltwg.txt'

GENERATION_MAPPING = {'Wind': 'wind',
                      'Hydro': 'hydro',
                      'Fossil/Biomass': 'unknown',
                      'Nuclear': 'nuclear'}


def get_data(url, session=None):
    """Returns a pandas dataframe."""
    s=session or requests.Session()
    req = s.get(url)
    df = pd.read_table(StringIO(req.text), skiprows=5)

    return df


def timestamp_converter(timestamp):
    """Turns string representation of time into an aware datetime object."""

    dt_naive = datetime.strptime(timestamp, '%m/%d/%Y %H:%M')
    western = pytz.timezone('America/Los_Angeles')
    dt_aware = western.localize(dt_naive)

    return dt_aware


def data_processor(df, logger):
    """
    Takes a dataframe and drops all generation rows that are empty or more
    than 1 day old. Turns each row into a dictionary and removes any generation
    types that are unknown.
    Returns a list of tuples in the form (datetime, production).
    """

    df= df.dropna(thresh=2)
    df.columns = df.columns.str.strip()

    # 5min data for the last 24 hours.
    df = df.tail(288)
    df['Date/Time'] = df['Date/Time'].map(timestamp_converter)

    known_keys = GENERATION_MAPPING.keys() | {'Date/Time', 'Load'}
    column_headers = set(df.columns)

    unknown_keys = column_headers - known_keys

    for k in unknown_keys:
        logger.warning('New data {} seen in US-BPA data source'.format(k),
                        extra={'key': 'US-BPA'})

    keys_to_remove = unknown_keys | {'Load'}

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()

        dt = production.pop('Date/Time')
        dt = dt.to_datetime()
        mapped_production = {GENERATION_MAPPING[k]:v for k,v in production.items()
                             if k not in keys_to_remove}

        processed_data.append((dt, mapped_production))

    return processed_data


def fetch_production(zone_key='US-BPA', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
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

    raw_data = get_data(GENERATION_URL, session=session)
    processed_data = data_processor(raw_data, logger)

    data = []
    for item in processed_data:
        datapoint = {'zoneKey': zone_key,
                     'datetime': item[0],
                     'production': item[1],
                     'storage': {},
                     'source': 'bpa.gov'}

        data.append(datapoint)

    return data


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
