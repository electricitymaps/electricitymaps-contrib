#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""

from dateutil import parser, tz
from io import StringIO
from logging import getLogger
import datetime
import pandas as pd
import requests

GENERATION_URL = 'https://marketplace.spp.org/public-data-api/gen-mix/asFile'

EXCHANGE_URL = 'https://marketplace.spp.org/public-data-api/interchange-trend/asFile'

MAPPING = {'Wind': 'wind',
           'Nuclear': 'nuclear',
           'Hydro': 'hydro',
           'Solar': 'solar',
           'Natural Gas': 'gas',
           'Diesel Fuel Oil': 'oil',
           'Waste Disposal Services': 'biomass',
           'Coal': 'coal'
            }

TIE_MAPPING = {'US-MISO->US-SPP': ['AMRN', 'DPC', 'GRE', 'MDU', 'MEC', 'NSP', 'OTP']}

# NOTE
# Data sources return timestamps in GMT.
# Energy storage situation unclear as of 16/03/2018, likely to change quickly in future.


def get_data(url, session=None):
    """Returns a pandas dataframe."""

    s=session or requests.Session()
    req = s.get(url, verify=False)
    df = pd.read_csv(StringIO(req.text))

    return df


def data_processor(df, logger):
    """
    Takes a dataframe and logging instance as input.
    Checks for new generation types and logs awarning if any are found.
    Parses the dataframe row by row removing unneeded keys.
    Returns a list of 2 element tuples, each containing a datetime object
    and production dictionary.
    """

    # Remove leading whitespace in column headers.
    df.columns = df.columns.str.strip()

    keys_to_remove = {'GMT MKT Interval', 'Average Actual Load', 'Other', 'Waste Heat'}

    # Check for new generation columns.
    known_keys = MAPPING.keys() | keys_to_remove
    column_headers = set(df.columns)

    unknown_keys = column_headers - known_keys

    for heading in unknown_keys:
        logger.warning('New column \'{}\' present in US-SPP data source.'.format(
            heading), extra={'key': 'US-SPP'})

    keys_to_remove = keys_to_remove | unknown_keys

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()

        extra_unknowns = sum([production[k] for k in unknown_keys])
        production['unknown'] = production['Other'] + production['Waste Heat'] + extra_unknowns

        dt_aware = parser.parse(production['GMT MKT Interval'])

        for k in keys_to_remove:
            production.pop(k, None)

        mapped_production = {MAPPING.get(k,k):v for k,v in production.items()}

        processed_data.append((dt_aware, mapped_production))

    return processed_data


def fetch_production(zone_key = 'US-SPP', session=None, target_datetime=None, logger=getLogger(__name__)):
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

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_data = get_data(GENERATION_URL, session=session)
    processed_data = data_processor(raw_data, logger)

    data = []
    for item in processed_data:
        datapoint = {
          'zoneKey': zone_key,
          'datetime': item[0],
          'production': item[1],
          'storage': {},
          'source': 'spp.org'
        }
        data.append(datapoint)

    return data


# NOTE disabled until discrepancy in MISO SPP flows is resolved.
def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the last 24 hours of power exchange (in MW) between two zones
    Arguments:
    zone_key1           -- the first zone
    zone_key2           -- the second zone; order of the two zones in params doesn't matter
    session (optional)  -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_data = get_data(EXCHANGE_URL, session=session)
    sorted_codes = '->'.join(sorted([zone_key1, zone_key2]))

    try:
        exchange_ties = TIE_MAPPING[sorted_codes]
    except KeyError as e:
        raise NotImplementedError('The exchange {} is not implemented'.format(sorted_codes))

    # TODO check glossary for flow direction.

    exchange_data = []
    for index, row in raw_data.iterrows():
        all_exchanges = row.to_dict()

        dt_aware = parser.parse(all_exchanges['GMTTime'])

        flows = [all_exchanges[tie] for tie in exchange_ties]
        netflow = sum(flows)

        exchange = {
          'sortedZoneKeys': sorted_codes,
          'datetime': dt_aware,
          'netFlow': netflow,
          'source': 'spp.org'
        }

        exchange_data.append(exchange)

    return exchange_data


def fetch_load_forecast(zone_key='US-SPP', session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the load forecast (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'US-SPP',
      'datetime': '2017-01-01T00:00:00Z',
      'value': 28576.0,
      'source': 'mysource.com'
    }
    """

    if not target_datetime:
        raise NotImplementedError("This parser requires a target datetime in format YYYYMMDD.")

    if isinstance(target_datetime, datetime.datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    LOAD_URL = 'https://marketplace.spp.org/file-api/download/mtlf-vs-actual?path=%2F{0}%2F{1:02d}%2F{2:02d}%2FOP-MTLF-{0}{1:02d}{2:02d}0000.csv'.format(dt.year, dt.month, dt.day)

    raw_data = get_data(LOAD_URL)

    data = []
    for index, row in raw_data.iterrows():
        forecast = row.to_dict()

        dt = parser.parse(forecast['GMTIntervalEnd']).replace(tzinfo=tz.gettz('Etc/GMT'))
        load = float(forecast['MTLF'])

        datapoint = {
                     'datetime': dt,
                     'value': load,
                     'zoneKey': zone_key,
                     'source': 'spp.org'
                     }

        data.append(datapoint)

    return data


def fetch_wind_solar_forecasts(zone_key='US-SPP', session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the load forecast (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'US-SPP',
      'datetime': '2017-01-01T00:00:00Z',
      'value': 28576.0,
      'source': 'mysource.com'
    }
    """

    if not target_datetime:
        raise NotImplementedError("This parser requires a target datetime in format YYYYMMDD.")

    if isinstance(target_datetime, datetime.datetime):
        dt = target_datetime
    else:
        dt = parser.parse(target_datetime)
    FORECAST_URL = 'https://marketplace.spp.org/file-api/download/midterm-resource-forecast?path=%2F{0}%2F{1:02d}%2F{2:02d}%2FOP-MTRF-{0}{1:02d}{2:02d}0000.csv'.format(dt.year, dt.month, dt.day)

    raw_data = get_data(FORECAST_URL)

    # sometimes there is a leading whitespace in column names
    raw_data.columns = raw_data.columns.str.lstrip()

    data = []
    for index, row in raw_data.iterrows():
        forecast = row.to_dict()

        dt = parser.parse(forecast['GMTIntervalEnd']).replace(tzinfo=tz.gettz('Etc/GMT'))

        try:
            solar = float(forecast['Wind Forecast MW'])
            wind = float(forecast['Solar Forecast MW'])
        except ValueError:
            # can be NaN
            continue

        datapoint = {
                     'datetime': dt,
                     'production': {
                        'solar': solar,
                        'wind': wind,
                     },
                     'zoneKey': zone_key,
                     'source': 'spp.org'
                     }

        data.append(datapoint)

    return data


if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
    # print('fetch_exchange() -> ')
    # print(fetch_exchange('US-MISO', 'US-SPP'))
    print('fetch_load_forecast() -> ')
    print(fetch_load_forecast(target_datetime='20190125'))
    print('fetch_wind_solar_forecasts() -> ')
    print(fetch_wind_solar_forecasts(target_datetime='20190125'))
