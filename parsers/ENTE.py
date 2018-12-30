#!/usr/bin/env python3

# This parser gets all real time interconnection flows from the
# Central American Electrical Interconnection System (SIEPAC).

import arrow
import pandas as pd

# map for reference
# http://www.enteoperador.org/newsite/flash/SER.html
DATA_URL = 'http://www.enteoperador.org/newsite/flash/data.csv'

CSV_MAPPING = {'GT->MX': ('MXGU', 'MXGUN'),
               'GT->SV': ('GUES', 'GUESN'),
               'GT->HN': ('GUHO', 'GUHON'),
               'HN->SV': ('ESHO', 'ESHON'),
               # 'HN->NI': ('HONI', 'HONIN'), NOTE bug in direction
               'CR->NI': ('NICR', 'NICRN'),
               'CR->PA': ('CRPA', 'CRPAN')}


def extract_exchange(df, exchange):
    """
    Extracts flow value and direction for a given exchange.
    Returns a float.
    """
    search_values = CSV_MAPPING[exchange]
    interconnection = df.iloc[0][search_values[0]], df.iloc[0][search_values[1]]
    direction = direction_finder(exchange, interconnection[1])

    flow = interconnection[0]*direction

    return flow


def direction_finder(exchange, logic):
    """Direction of electricity flow on ENTE map is shown by arrows.
    These arrows are controlled by booleans in the returned data.
    Due to differences in how ENTE and EM order exchanges (e.g. ESHO vs HN->SV)
    sometimes multiplying by -1 is needed.
    Returns an integer.
    """
    if exchange in ['GT->SV', 'GT->HN', 'HN->SV', 'CR->NI']:
        if logic == 0:
            return -1
        else:
            return 1
    else:
        if logic == 1:
            return -1
        else:
            return 1


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """
    Gets an exchange pair from the SIEPAC system.
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'CR->PA',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zones = '->'.join(sorted([zone_key1, zone_key2]))

    if sorted_zones not in CSV_MAPPING.keys():
        raise NotImplementedError('This exchange is not implemented.')

    raw_data = pd.read_csv(DATA_URL, index_col=False)
    flow = extract_exchange(raw_data, sorted_zones)
    dt = arrow.now('UTC-6').floor('minute')

    exchange = {'sortedZoneKeys': sorted_zones,
                'datetime': dt.datetime,
                'netFlow': flow,
                'source': 'enteoperador.org'}

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print('fetch_exchange(CR, PA) ->')
    print(fetch_exchange('CR', 'PA'))
    print('fetch_exchange(CR, NI) ->')
    print(fetch_exchange('CR', 'NI'))
    # print('fetch_exchange(HN, NI) ->')
    # print(fetch_exchange('HN', 'NI'))
    print('fetch_exchange(GT, MX) ->')
    print(fetch_exchange('GT', 'MX'))
    print('fetch_exchange(GT, SV) ->')
    print(fetch_exchange('GT', 'SV'))
    print('fetch_exchange(GT, HN) ->')
    print(fetch_exchange('GT', 'HN'))
    print('fetch_exchange(HN, SV) ->')
    print(fetch_exchange('HN', 'SV'))
