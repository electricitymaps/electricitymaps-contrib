#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# More info:
# https://www.bchydro.com/energy-in-bc/our_system/transmission/transmission-system/actual-flow-data.html

timezone = 'Canada/Pacific'


def fetch_exchange(zone_key1=None, zone_key2=None, session=None, target_datetime=None, logger=None):
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

    r = session or requests.session()
    url = 'https://www.bchydro.com/bctc/system_cms/actual_flow/latest_values.txt'
    response = r.get(url)
    obj = response.text.split('\r\n')[1].replace('\r', '').split(',')

    datetime = arrow.get(
        arrow.get(obj[0], 'DD-MMM-YY HH:mm:ss').datetime, timezone).datetime

    if (zone_key1 == 'CA-BC' and zone_key2 == 'US-BPA'):
        sortedZoneKeys = 'CA-BC->US-BPA'
        netFlow = float(obj[1])
    elif (zone_key1 == 'CA-AB' and zone_key2 == 'CA-BC'):
        sortedZoneKeys = 'CA-AB->CA-BC'
        netFlow = -1 * float(obj[2])
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    return {
        'datetime': datetime,
        'sortedZoneKeys': sortedZoneKeys,
        'netFlow': netFlow,
        'source': 'bchydro.com',
    }


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_exchange(CA-BC, US-BPA) ->')
    print(fetch_exchange('CA-BC', 'US-BPA'))
    print('fetch_exchange(CA-AB, CA-BC) ->')
    print(fetch_exchange('CA-AB', 'CA-BC'))
