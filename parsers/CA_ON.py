#!/usr/bin/env python3

import datetime

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

from bs4 import BeautifulSoup

MAP_GENERATION = {
    'BIOFUEL': 'biomass',
    'GAS': 'gas',
    'HYDRO': 'hydro',
    'NUCLEAR': 'nuclear',
    'SOLAR': 'solar',
    'WIND': 'wind'
}

timezone = 'Canada/Eastern'


def fetch_production(zone_key='CA-ON', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    r = session or requests.session()
    url = 'http://www.ieso.ca/-/media/files/ieso/uploaded/chart/generation_fuel_type_multiday.xml?la=en'
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = {}

    start_datetime = arrow.get(
        arrow.get(soup.find_all('startdate')[0].contents[0]).datetime, timezone)

    # Iterate over all datasets (production types)
    for item in soup.find_all('dataset'):
        key = item.attrs['series']
        for rowIndex, row in enumerate(item.find_all('value')):
            if not len(row.contents):
                continue
            if rowIndex not in data:
                data[rowIndex] = {
                    'datetime': start_datetime.replace(hours=+rowIndex).datetime,
                    'zoneKey': zone_key,
                    'production': {
                        'coal': 0
                    },
                    'storage': {},
                    'source': 'ieso.ca',
                }
            data[rowIndex]['production'][MAP_GENERATION[key]] = \
                float(row.contents[0])

    return [data[k] for k in sorted(data.keys())]


def fetch_price(zone_key='CA-ON', session=None, target_datetime=None, logger=None):
    """Requests the last known power price of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://www.ieso.ca/-/media/files/ieso/uploaded/chart/price_multiday.xml?la=en'
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    data = {}

    start_datetime = arrow.get(
        arrow.get(soup.find_all('startdate')[0].contents[0]).datetime, timezone)

    # Iterate over all datasets (production types)
    for item in soup.find_all('dataset'):
        key = item.attrs['series']
        if key != 'HOEP':
            continue
        for rowIndex, row in enumerate(item.find_all('value')):
            if not len(row.contents):
                continue
            if rowIndex not in data:
                data[rowIndex] = {
                    'datetime': start_datetime.replace(hours=+rowIndex).datetime,
                    'zoneKey': zone_key,
                    'currency': 'CAD',
                    'source': 'ieso.ca',
                }
            data[rowIndex]['price'] = \
                float(row.contents[0])

    return [data[k] for k in sorted(data.keys())]

    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
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

    exchange_maps = {
        'MANITOBA': 'CA-MB->CA-ON',
        'MANITOBA SK': 'CA-MB->CA-ON',
        'MICHIGAN': 'CA-ON->US-MISO',
        'MINNESOTA': 'CA-ON->US-MISO',
        'NEW-YORK': 'CA-ON->US-NY',
        'PQ.AT': 'CA-ON->CA-QC',
        'PQ.B5D.B31L': 'CA-ON->CA-QC',
        'PQ.D4Z': 'CA-ON->CA-QC',
        'PQ.D5A': 'CA-ON->CA-QC',
        'PQ.H4Z': 'CA-ON->CA-QC',
        'PQ.H9A': 'CA-ON->CA-QC',
        'PQ.P33C': 'CA-ON->CA-QC',
        'PQ.Q4C': 'CA-ON->CA-QC',
        'PQ.X2Y': 'CA-ON->CA-QC'
    }

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys not in exchange_maps.values():
        raise NotImplementedError('This exchange pair is not implemented')

    # TODO: verify timezone handling vs filename on server
    dt = arrow.get(arrow.get(target_datetime, timezone))
    filename = dt.format('YYYYMMDD')

    r = session or requests.session()
    #url = 'http://reports.ieso.ca/public/IntertieScheduleFlow/PUB_IntertieScheduleFlow_{}.xml'.format(filename)
    #response = r.get(url)
    #soup = BeautifulSoup(response.text, 'html.parser')
    with open('PUB_IntertieScheduleFlow_{}.xml'.format(filename)) as f:
        # temporary for faster debugging...
        soup = BeautifulSoup(f.read(), 'html5lib')

    interties = soup.find_all('intertiezone')

    for intertie in interties:
        intertie_name = intertie.find('intertiezonename').text

        if intertie_name not in exchange_maps:
            logger.warning('CA-ON: unrecognized intertie name {}, please implement it!'.format(intertie_name))
            continue

        mapping = exchange_maps[intertie_name]
        print(intertie_name, mapping)

        if not mapping == sorted_zone_keys:
            # we're not interested in data for this zone, skip it
            continue

        # in the XML, flow into Ontario is always negative.
        # in EM, for 'CA-MB->CA-ON', flow into Ontario is positive.
        if mapping.startswith('CA-ON->'):
            direction = 1
        else:
            direction = -1

        actuals = intertie.find_all('actual')

        data = []

        for actual in actuals:
            hour = int(actual.find('hour').text) - 1
            minute = (int(actual.find('interval').text) - 1) * 5
            flow = float(actual.find('flow').text) * direction

            data.append(
                {
                    'datetime': datetime.datetime(dt.year, dt.month, dt.day, hour, minute),  # TODO: timezone?
                    'sortedZoneKeys': sorted_zone_keys,
                    'netFlow': flow,
                    'source': 'ieso.ca'
                }
            )

            # TODO: we will need to add up values for same datetime for exchanges with more than one intertie

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    #print(fetch_production())
    print('fetch_price() ->')
    #print(fetch_price())
    print('fetch_exchange("CA-ON", "US-NY") ->')
    #print(fetch_exchange("CA-ON", "US-NY"))
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=datetime.datetime(2018, 4, 14, 12, 0)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=datetime.datetime(2018, 4, 14, 12, 0)))
    # TODO: give examples of exchange right now, and exchange 2 months ago
