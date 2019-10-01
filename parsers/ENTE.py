#!/usr/bin/env python3

import arrow
import requests


# This parser gets all real time interconnection flows from the
# Central American Electrical Interconnection System (SIEPAC).

# map for reference
# https://www.enteoperador.org/flujos-regionales-en-tiempo-real/

DATA_URL = 'https://mapa.enteoperador.org/WebServiceScadaEORRest/webresources/generic'

JSON_MAPPING = {"GT->MX": "2LBR.LT400.1FR2-2LBR-01A.-.MW",
                "GT->SV": "3SISTEMA.LT230.INTER_NET_GT.CMW.MW",
                "GT->HN": "4LEC.LT230.2FR4-4LEC-01B.-.MW",
                "HN->SV": "3SISTEMA.LT230.INTER_NET_HO.CMW.MW",
                "HN->NI": "5SISTEMA.LT230.INTER_NET_HN.CMW.MW",
                "CR->NI": "5SISTEMA.LT230.INTER_NET_CR.CMW.MW",
                "CR->PA": "6SISTEMA.LT230.INTER_NET_PAN.CMW.MW"}


def extract_exchange(raw_data, exchange):
    """
    Extracts flow value and direction for a given exchange.
    Returns a float or None.
    """
    search_value = JSON_MAPPING[exchange]

    interconnection = None
    for datapoint in raw_data:
        if datapoint['nombre'] == search_value:
            interconnection = float(datapoint['value'])

    if interconnection is None:
        return None

    # positive and negative flow directions do not always correspond to EM ordering of exchanges
    if exchange in ['GT->SV', 'GT->HN', 'HN->SV', 'CR->NI', 'HN->NI']:
        interconnection *= -1

    return interconnection


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

    if sorted_zones not in JSON_MAPPING.keys():
        raise NotImplementedError('This exchange is not implemented.')

    s = session or requests.Session()

    raw_data = s.get(DATA_URL).json()
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
    print('fetch_exchange(CR, NI) ->') #wrong way
    print(fetch_exchange('CR', 'NI'))
    print('fetch_exchange(HN, NI) ->')
    print(fetch_exchange('HN', 'NI'))
    print('fetch_exchange(GT, MX) ->')
    print(fetch_exchange('GT', 'MX'))
    print('fetch_exchange(GT, SV) ->') #wrong way
    print(fetch_exchange('GT', 'SV'))
    print('fetch_exchange(GT, HN) ->') #wrong way
    print(fetch_exchange('GT', 'HN'))
    print('fetch_exchange(HN, SV) ->') #wrong way
    print(fetch_exchange('HN', 'SV'))
