#!/usr/bin/env python3

# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from ree import BalearicIslands
from .lib.exceptions import ParserException


def fetch_consumption(zone_key='ES-IB', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    ses = session or Session()

    # TODO: Remove verify SSL config when working without it.
    responses = BalearicIslands(ses, verify=False).get_all()
    if not responses:
        raise ParserException("ES-IB", "No response")
    else:
        data = []

        for response in responses:
            response_data = {
                'zoneKey': zone_key,
                'datetime': get(response.timestamp).datetime,
                'consumption': response.demand,
                'source': 'demanda.ree.es'
            }

            data.append(response_data)

        return data


def fetch_production(zone_key='ES-IB', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    ses = session or Session()

    # TODO: Remove verify SSL config when working without it.
    responses = BalearicIslands(ses, verify=False).get_all()

    if not responses:
        raise ParserException("ES-IB", "No response")
    else:

        data = []

        for response in responses:
            response_data = {
                'zoneKey': zone_key,
                'datetime': get(response.timestamp).datetime,
                'production': {
                    'coal': response.carbon,
                    'gas': round(response.gas + response.combined, 2),
                    'solar': response.solar,
                    'oil': round(response.vapor + response.diesel, 2),
                    'wind': response.wind,
                    'hydro': response.hydraulic,
                    'biomass': 0.0,
                    'nuclear': 0.0,
                    'geothermal': 0.0,
                    'unknown': response.unknown()
                },
                'storage': {
                    'hydro': 0.0,
                    'battery': 0.0
                },
                'source': 'demanda.ree.es',
            }

            data.append(response_data)

        return data


def fetch_exchange(zone_key1='ES', zone_key2='ES-IB', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    ses = session or Session()

    # TODO: Remove verify SSL config when working without it.
    responses = BalearicIslands(ses, verify=False).get_all()
    if not responses:
        raise ParserException("ES-IB", "No response")
    else:

        data = []
        for response in responses:

            sorted_zone_keys = sorted([zone_key1, zone_key2])
            net_flow = response.link['pe_ma']

            response_data = {
                'sortedZoneKeys': '->'.join(sorted_zone_keys),
                'datetime': get(response.timestamp).datetime,
                'netFlow': net_flow if zone_key1 == sorted_zone_keys[0] else -1 * net_flow,
                'source': 'demanda.ree.es',
            }

            data.append(response_data)

        return data


if __name__ == '__main__':
    session = Session
    print(fetch_consumption('ES-IB', session))
    print(fetch_production('ES-IB', session))
    print(fetch_exchange('ES', 'ES-IB', session))
