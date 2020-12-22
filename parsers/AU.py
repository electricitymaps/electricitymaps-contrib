#!/usr/bin/env python3

import logging, json

# The arrow library is used to handle datetimes
import arrow
import numpy as np
import pandas as pd
# The request library is used to fetch content through HTTP
import requests

# It appears that the interconnectors are named according to positive flow.
# That is, NSW1-QLD1 reports positive values when there is flow from NSW to QLD,
# and negative values when flow is from QLD to NSW.
# To verify, compare with flows shown on
# http://aemo.com.au/Electricity/National-Electricity-Market-NEM/Data-dashboard#nem-dispatch-overview
EXCHANGE_MAPPING_DICTIONARY = {
    'AUS-NSW->AUS-QLD': {
        'region_id': 'QLD1',
        'interconnector_names': ['N-Q-MNSP1', 'NSW1-QLD1'],
        'directions': [1, 1]
    },
    'AUS-NSW->AUS-VIC': {
        'region_id': 'NSW1',
        'interconnector_names': ['VIC1-NSW1'],
        'directions': [-1]
    },
    'AUS-SA->AUS-VIC': {
        'region_id': 'VIC1',
        'interconnector_names': ['V-SA', 'V-S-MNSP1'],
        'directions': [-1, -1]
    },
    'AUS-TAS->AUS-VIC': {
        'region_id': 'VIC1',
        'interconnector_names': ['T-V-MNSP1'],
        'directions': [1]
    },
}


def fetch_exchange(zone_key1=None, zone_key2=None, session=None, target_datetime=None,
                   logger=logging.getLogger(__name__)):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))
    mapping = EXCHANGE_MAPPING_DICTIONARY[sorted_zone_keys]

    r = session or requests.session()
    url = 'https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY'
    # A User-Agent is required or the server gives us a 403 
    headers = { 'User-Agent': 'electricitymap.org' }
    response = r.get(url, headers = headers)
    obj = list(filter(lambda o: o['REGIONID'] == mapping['region_id'],
                      response.json()['ELEC_NEM_SUMMARY']))[0]

    flows = json.loads(obj['INTERCONNECTORFLOWS'])
    net_flow = 0
    import_capacity = 0
    export_capacity = 0
    for i in range(len(mapping['interconnector_names'])):
        interconnector_name = mapping['interconnector_names'][i]
        interconnector = list(filter(lambda f: f['name'] == interconnector_name, flows))[0]
        direction = mapping['directions'][i]
        net_flow += direction * interconnector['value']
        import_capacity += direction * interconnector[
            'importlimit' if direction == 1 else 'exportlimit']
        export_capacity += direction * interconnector[
            'exportlimit' if direction == 1 else 'importlimit']

    data = {
        'sortedZoneKeys': sorted_zone_keys,
        'netFlow': net_flow,
        'capacity': [import_capacity, export_capacity],  # first one should be negative
        'source': 'aemo.com.au',
        'datetime': arrow.get(arrow.get(obj['SETTLEMENTDATE']).datetime, 'Australia/NSW').shift(
            minutes=-5).datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    # print("fetch_exchange('AUS-NSW', 'AUS-QLD') ->")
    # print(fetch_exchange('AUS-NSW', 'AUS-QLD'))
    # print("fetch_exchange('AUS-NSW', 'AUS-VIC') ->")
    # print(fetch_exchange('AUS-NSW', 'AUS-VIC'))
    # print("fetch_exchange('AUS-VIC', 'AUS-SA') ->")
    # print(fetch_exchange('AUS-VIC', 'AUS-SA'))
    # print("fetch_exchange('AUS-VIC', 'AUS-TAS') ->")
    # print(fetch_exchange('AUS-VIC', 'AUS-TAS'))
