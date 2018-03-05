#!/usr/bin/env python3
import logging
import datetime

# The arrow library is used to handle datetimes
from json import JSONDecodeError

import arrow
# The request library is used to fetch content through HTTP
import requests


def fetch_production(country_code='FR', session=None, target_datetime: datetime.datetime=None,
                     logger: logging.Logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    country_code: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. If past data is not available, raise a NotImplementedError. Beware that the
      provided target_datetime is UTC.
    logger: an instance of a `logging.logger`. Information logged will be publicly available so that
      correct execution of the logger can be checked

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
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
    r = session or requests.session()
    if target_datetime is None:
        url = 'https://api.someservice.com/v1/productionmix/latest'
    else:
        # WHEN HISTORICAL DATA IS AVAILABLE
        # convert target datetime to local datetime
        url_date = arrow.get(target_datetime).to("America/Argentina/Buenos_Aires")
        url = 'https://api.someservice.com/v1/productionmix/{}'.format(url_date)

        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError('This parser is not yet able to parse past dates')

    try:
        response = r.get(url)
        assert response.status_code == 200
    except:
        logger.exception('Exception when fetching production for {}: error when calling '
                         'url={}'.format(country_code, url))
        return

    obj = response.json()

    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'someservice.com',
    }
    for item in obj['productionMix']:
        # All production values should be >= 0
        data['production'][item['key']] = item['value']  # Should be a floating point value

    for item in obj['storage']:
        # Positive storage means energy is stored
        # Negative storage means energy is generated from the storage system
        data['storage'][item['key']] = item['value']  # Should be a floating point value

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


def fetch_price(country_code='FR', session=None, target_datetime=None, logger=None):
    """Requests the last known power price of a given country

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. If past data is not available, raise a NotImplementedError. Beware that the
      provided target_datetime is UTC.

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'https://api.someservice.com/v1/price/latest'

    try:
        response = r.get(url)
        assert response.status_code == 200
    except:
        logger.exception('Exception when fetching price for {}: error when calling '
                         'url={}'.format(country_code, url))
        return

    try:
        obj = response.json()
    except JSONDecodeError:
        logger.exception('Exception when fetching price for {}: response could not be parsed '
                         'as json. response={}'.format(country_code, response.text))
        return

    data = {
        'countryCode': country_code,
        'currency': 'EUR',
        'price': obj['price'],
        'source': 'someservice.com',
    }

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


def fetch_exchange(country_code1='DK', country_code2='NO', session=None, target_datetime=None,
                   logger=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. If past data is not available, raise a NotImplementedError. Beware that the
      provided target_datetime is UTC.

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'https://api.someservice.com/v1/exchange/latest?from={}&to={}'.format(
        country_code1, country_code2)

    try:
        response = r.get(url)
        assert response.status_code == 200
    except:
        logger.exception('Exception when fetching exchange for zones {} and {}: error when calling '
                         'url={}'.format(country_code1, country_code2, url))
        return

    try:
        obj = response.json()
    except JSONDecodeError:
        logger.exception('Exception when fetching exchange for zones {} and {}: response could not '
                         'be parsed as json. response={}'.format(country_code1, country_code2,
                                                                 response.text))
        return

    data = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'source': 'someservice.com',
    }

    # Country codes are sorted in order to enable easier indexing in the database
    sorted_country_codes = sorted([country_code1, country_code2])
    # Here we assume that the net flow returned by the api is the flow from
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    net_flow = obj['exchange']
    # The net flow to be reported should be from the first country to the second
    # (sorted alphabetically). This is NOT necessarily the same direction as the flow
    # from country1 to country2
    data['netFlow'] = net_flow if country_code1 == sorted_country_codes[0] else -1 * net_flow

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange(DK, NO) ->')
    print(fetch_exchange('DK', 'NO'))
