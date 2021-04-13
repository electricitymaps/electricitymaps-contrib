# coding=utf-8
"""Parser for Moldova."""

import arrow
from operator import itemgetter
import requests

TYPE_MAPPING = {
    u'tmva476': 'hydro',  # NHE Costeşti (run-of-river) #2 index
    u'tmva112': 'hydro',  # NHE Dubăsari (run-of-river) #4 index
    u'tmva367': 'gas',  # CET Nord (CHPP) #3 index
    u'tmva42': 'gas',  # CET-1 Chişinău (CHPP) #6 index
    u'tmva378': 'gas',  # CET-2 Chişinău (CHPP) #5 index
    u'tmva1024': 'gas',  # CERS Moldovenească (fuel mix 2017 99.92% gas, 0.08% oil) #7 index
}

display_url = 'http://www.moldelectrica.md/ro/activity/system_state'
data_url = 'http://www.moldelectrica.md/utils/load4.php'


def get_data(session=None):
    """ Returns generation data as a list of floats."""

    s = session or requests.Session()

    #In order for the data url to return data, cookies from the display url must be obtained then reused.
    response = s.get(display_url, verify=False)
    data_response = s.get(data_url, verify=False)
    raw_data = data_response.text
    try:
        data = [float(i) for i in raw_data.split(',')]
    except:
        raise Exception("Not able to parse received data. Check that the specifed URL returns correct data.")

    return data


def fetch_production(zone_key='MD', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    grid_status = get_data(session=session)
    production = {'solar': None, 'wind': None, 'biomass': None, 'nuclear': 0.0}

    production['gas'] = sum(itemgetter(3, 5, 6)(grid_status))
    production['hydro'] = sum(itemgetter(2, 4)(grid_status))
    production['unknown'] = grid_status[7]

    consumption = grid_status[-5]

    dt = arrow.now('Europe/Chisinau').datetime

    datapoint = {
        'zoneKey': zone_key,
        'datetime': dt,
        'consumption': consumption,
        'production': production,
        'storage': {},
        'source': 'moldelectrica.md'
    }

    return datapoint


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """
    Requests the last known power exchange (in MW) between two countries.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))

    exchange_status = get_data(session=session)

    if sortedZoneKeys == 'MD->UA':
        netflow = -1 * exchange_status[-3]
    elif sortedZoneKeys == 'MD->RO':
        netflow = -1 * exchange_status[-2]
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    dt = arrow.now('Europe/Chisinau').datetime

    exchange = {
        'sortedZoneKeys': sortedZoneKeys,
        'datetime': dt,
        'netFlow': netflow,
        'source': 'moldelectrica.md'
    }

    return exchange


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(MD, UA) ->')
    print(fetch_exchange('MD', 'UA'))
    print('fetch_exchange(MD, RO) ->')
    print(fetch_exchange('MD', 'RO'))
