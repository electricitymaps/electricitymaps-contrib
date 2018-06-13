#!/usr/bin/env python3

"""Parser for the SVERI area of the USA."""

from datetime import datetime, timedelta
from io import StringIO
import logging
import pandas as pd
import pytz
import requests


# SVERI = Southwest Variable Energy Resource Initiative
# https://sveri.energy.arizona.edu/#howto

# SVERI participants include Arizona's G&T Cooperatives, Arizona Public Service,
# El Paso Electric, Imperial Irrigation District, Public Service Company of New Mexico,
# Salt River Project, Tucson Electric Power and the Western Area Power Administration’s Desert Southwest Region.

#TODO geothermal is negative, 15 to add to request
GENERATION_URL = 'https://sveri.energy.arizona.edu/api?ids=1,2,4,5,6,7,8,16&saveData=true'

GENERATION_MAPPING = {'Solar Aggregate (MW)': 'solar',
                      'Wind Aggregate (MW)': 'wind',
                      'Hydro Aggregate (MW)': 'hydro',
                      'Coal Aggregate (MW)': 'coal',
                      'Gas Aggregate (MW)': 'gas',
                      'Other Fossil Fuels Aggregate (MW)': 'unknown',
                      'Nuclear Aggregate (MW)': 'nuclear',
                      #'Geothermal Aggregate (MW)': 'geothermal',
                      'Biomass/gas Aggregate (MW)': 'biomass'}


def query_api(limits, session=None):
    """Makes a request to the SVERI api and returns a dataframe."""

    s = session or requests.Session()
    url = GENERATION_URL + '&startDate={}&endDate={}'.format(limits[0], limits[1])
    data_req = s.get(url)
    df = pd.read_csv(StringIO(data_req.text))

    return df


def timestamp_converter(timestamp):
    """Turns string representation of timestamp into an aware datetime object."""

    dt_naive = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
    mountain = pytz.timezone('America/Dawson_Creek')
    dt_aware = mountain.localize(dt_naive)

    return dt_aware


def data_processor(raw_data, logger):
    """
    Maps generation data to type, logging and removing unknown types.
    Returns a list of tuples in the form (datetime, production).
    """

    mapped_df = raw_data.rename(columns=lambda x: GENERATION_MAPPING.get(x,x))
    actual_keys = set(mapped_df.columns)
    expected_keys = set(GENERATION_MAPPING.values()) | {'Time (MST)'}
    unknown_keys = actual_keys - expected_keys

    for k in unknown_keys:
        logger.warning('New type {} seen in US-SVERI data source'.format(k),
                        extra={'key': 'US-SVERI'})
        mapped_df.drop(k, axis=1, inplace=True)

    processed_data = []
    for index, row in mapped_df.iterrows():
        production = row.to_dict()

        dt = production.pop('Time (MST)')
        dt = timestamp_converter(dt)
        processed_data.append((dt, production))

    return processed_data


def fetch_production(zone_key='US-SVERI', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional): used in case a parser is able to fetch multiple zones
    session: request session passed in order to re-use an existing session
    target_datetime: datetime object that allows historical data to be fetched
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': None,
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

    if target_datetime is None:
        target_datetime = datetime.now()

    start_date = target_datetime.strftime('%Y-%m-%d')
    shift_date = target_datetime + timedelta(days=1)
    end_date = shift_date.strftime('%Y-%m-%d')
    limits = (start_date, end_date)

    raw_data = query_api(limits, session=session)
    processed_data = data_processor(raw_data, logger)

    data = []
    for item in processed_data:
        datapoint = {
          'zoneKey': zone_key,
          'datetime': item[0],
          'production': item[1],
          'storage': {},
          'source': 'sveri.energy.arizona.edu'
        }

        data.append(datapoint)

    return data


if __name__ == '__main__':
    "Main method, never used by the Electricity Map backend, but handy for testing."

    print('fetch_production() ->')
    print(fetch_production())
