#!usr/bin/env python3

"""Parser for the Southwest Power Pool area of the United States."""

from dateutil import parser, tz
from io import StringIO
from logging import getLogger
import pandas as pd
import requests

generation_url = 'https://marketplace.spp.org/public-data-api/gen-mix/asFile'

exchange_url = 'https://marketplace.spp.org/public-data-api/interchange-trend/asFile'

mapping = {'coal': 'coal',
           'unknown': 'unknown',
           'Wind': 'wind',
           'Nuclear': 'nuclear',
           'Hydro': 'hydro',
           'Solar': 'solar',
           'Natural Gas': 'gas',
           'Diesel Fuel Oil': 'oil',
           'Waste Disposal Services': 'biomass'
            }

tie_mapping = {'US-MISO->US-SPP': ['AMRN', 'DPC', 'GRE', 'MDU', 'MEC', 'NSP', 'OTP']}

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

    keys_to_remove = ['Coal Market', 'Coal Self', 'GMT MKT Interval', 'Average Actual Load',
                      'Other', 'Waste Heat']

    # Check for new generation columns.
    known_keys = list(mapping.keys()) + keys_to_remove
    column_headers = list(df)

    unknown_keys = []
    for heading in column_headers:
        if heading not in known_keys:
            logger.warning('New column \'{}\' present in US-SPP data source.'.format(
                heading), extra={'key': 'US-SPP'})
            unknown_keys.append(heading)

    keys_to_remove += unknown_keys

    processed_data = []
    for index, row in df.iterrows():
        production = row.to_dict()
        production['coal'] = production['Coal Market'] + production['Coal Self']

        extra_unknowns = sum([production[k] for k in unknown_keys])
        production['unknown'] = production['Other'] + production['Waste Heat'] + extra_unknowns

        dt_aware = parser.parse(production['GMT MKT Interval'])

        for k in keys_to_remove:
            production.pop(k, None)

        mapped_production = {mapping.get(k,k):v for k,v in production.items()}

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

    raw_data = get_data(generation_url, session=session)
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

    raw_data = get_data(exchange_url, session=session)
    sorted_codes = '->'.join(sorted([zone_key1, zone_key2]))

    try:
        exchange_ties = tie_mapping[sorted_codes]
    except KeyError as e:
        raise NotImplementedError('This exchange pair is not implemented')

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


if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
    # print('fetch_exchange() -> ')
    # print(fetch_exchange('US-MISO', 'US-SPP'))
