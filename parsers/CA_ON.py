#!/usr/bin/env python3

import logging
import xml.etree.ElementTree as ET

# The arrow library is used to handle datetimes
import arrow

# BeautifulSoup processes markup, this could be migrated to use xml library
from bs4 import BeautifulSoup

# pytz gets tzinfo objects
import pytz

# The request library is used to fetch content through HTTP
import requests

# pandas processes tabular data
import pandas as pd


timezone = 'Canada/Eastern'
tz_obj = pytz.timezone(timezone)

# fuel types used by IESO
MAP_GENERATION = {
    'BIOFUEL': 'biomass',
    'GAS': 'gas',
    'HYDRO': 'hydro',
    'NUCLEAR': 'nuclear',
    'SOLAR': 'solar',
    'WIND': 'wind'
}

# exchanges and sub-exchanges used by IESO
MAP_EXCHANGE = {
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

PRODUCTION_URL = 'http://reports.ieso.ca/public/GenOutputCapability/PUB_GenOutputCapability_{YYYYMMDD}.xml'
EXCHANGES_URL = 'http://reports.ieso.ca/public/IntertieScheduleFlow/PUB_IntertieScheduleFlow_{YYYYMMDD}.xml'

XML_NS_TEXT = '{http://www.theIMO.com/schema}'


def fetch_production(zone_key='CA-ON', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    """Requests the last known production mix (in MW) of a given region

    Arguments:
    zone_key (optional): ignored here, only information for CA-ON is returned
    session (optional): request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically

    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'CA-ON',
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

    dt = arrow.get(target_datetime).to(tz_obj).replace(hour=0, minute=0, second=0, microsecond=0)

    r = session or requests.session()
    url = PRODUCTION_URL.format(YYYYMMDD=dt.format('YYYYMMDD'))
    response = r.get(url)

    if not response.ok:
        # Data is generally available for past 3 months. Requesting files older than this
        # returns an HTTP 404 error.
        logger.info('CA-ON: failed getting requested production data for datetime {} from IESO server'.format(dt))
        return []

    xml = ET.fromstring(response.text)

    generators = xml\
        .find(XML_NS_TEXT + 'IMODocBody')\
        .find(XML_NS_TEXT + 'Generators')\
        .findall(XML_NS_TEXT + 'Generator')

    def production_or_zero(output):
        # Sometimes the XML data has no "EnergyMW" tag for a given plant at a given hour.
        # The report XSL formats this as "N/A" - we return 0
        tag = output.find(XML_NS_TEXT + 'EnergyMW')
        if tag is not None:
            return tag.text
        else:
            return 0

    # flat iterable of per-generator-plant productions per time from the XML data
    all_productions = (
        {
            'name': generator.find(XML_NS_TEXT + 'GeneratorName').text,
            'fuel': MAP_GENERATION[
                generator.find(XML_NS_TEXT + 'FuelType').text
            ],
            'dt': dt.replace(hours=+int(
                output.find(XML_NS_TEXT + 'Hour').text
            )).datetime,
            'production': float(production_or_zero(output))
        }
        for generator in generators
        for output in generator.find(XML_NS_TEXT + 'Outputs').findall(XML_NS_TEXT + 'Output')
    )

    df = pd.DataFrame(all_productions)

    # group individual plants using the same fuel together for each time period
    by_fuel = df.groupby(['dt', 'fuel']).sum().unstack()
    # to debug, you can `print(by_fuel)` here, which gives a very pretty table

    by_fuel_dict = by_fuel['production'].to_dict('index')

    data = [
        {
            'datetime': time,
            'zoneKey': zone_key,
            'production': productions,
            'storage': {},
            'source': 'ieso.ca',
        }
        for time, productions in by_fuel_dict.items()
    ]

    # being constructed from a dict, data is not guaranteed to be in chronological order.
    # sort it for clean-ness and easier debugging.
    data = sorted(data, key=lambda dp: dp['datetime'])

    return data


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


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=logging.getLogger(__name__)):
    """Requests the last known power exchange (in MW) between two regions

    Arguments:
    zone_key1: the first region code
    zone_key2: the second region code; order of the two codes in params doesn't matter
    session: requests session passed in order to re-use an existing session,
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. The provided target_datetime is timezone-aware in UTC.
    logger: an instance of a `logging.Logger`; all raised exceptions are also logged automatically

    Return:
    A list of dictionaries in the form:
    [{
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }]
    """

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))

    if sorted_zone_keys not in MAP_EXCHANGE.values():
        raise NotImplementedError('This exchange pair is not implemented')

    dt = arrow.get(target_datetime).to(tz_obj).replace(hour=0, minute=0, second=0, microsecond=0)

    r = session or requests.session()
    url = EXCHANGES_URL.format(YYYYMMDD=dt.format('YYYYMMDD'))
    response = r.get(url)

    if not response.ok:
        # Data is generally available for past 3 months. Requesting files older than this
        # returns an HTTP 404 error.
        logger.info('CA-ON: failed getting requested exchange data for datetime {} from IESO server'.format(dt))
        return []

    xml = ET.fromstring(response.text)

    intertie_zones = xml\
        .find(XML_NS_TEXT + 'IMODocBody')\
        .findall(XML_NS_TEXT + 'IntertieZone')

    def flow_dt(flow):
        # The IESO day starts with Hour 1, Interval 1.
        # At 11:37, we might have data for up to Hour 11, Interval 12.
        # This means it is necessary to subtract 1 from the values
        # (otherwise we would have data for 12:00 already at 11:37).
        hour = int(flow.find(XML_NS_TEXT + 'Hour').text) - 1
        minute = (int(flow.find(XML_NS_TEXT + 'Interval').text) - 1) * 5

        return dt.replace(hours=+hour, minutes=+minute).datetime

    # flat iterable of per-intertie values per time from the XML data
    all_exchanges = (
        {
            'name': intertie.find(XML_NS_TEXT + 'IntertieZoneName').text,
            'dt': flow_dt(flow),
            'flow': float(flow.find(XML_NS_TEXT + 'Flow').text)
        }
        for intertie in intertie_zones
        for flow in intertie.find(XML_NS_TEXT + 'Actuals').findall(XML_NS_TEXT + 'Actual')
    )

    df = pd.DataFrame(all_exchanges)

    # verify that there haven't been new exchanges or sub-exchanges added
    all_exchange_names = set(df['name'].unique())
    known_exchange_names = set(MAP_EXCHANGE.keys())
    unknown_exchange_names = all_exchange_names - known_exchange_names
    if unknown_exchange_names:
        logger.warning('CA-ON: unrecognized intertie name(s) {}, please implement!'.format(unknown_exchange_names))

    # filter to only the sought exchanges
    sought_exchanges = [ieso_name for ieso_name, em_name in MAP_EXCHANGE.items() if sorted_zone_keys == em_name]
    df = df[df['name'].isin(sought_exchanges)]

    # in the XML, flow into Ontario is always negative.
    # in EM, for 'CA-MB->CA-ON', flow into Ontario is positive.
    if not sorted_zone_keys.startswith('CA-ON->'):
        df['flow'] *= -1

    # group flows for sub-interchanges together and sum them
    grouped = df.groupby(['dt']).sum()

    grouped_dict = grouped['flow'].to_dict()

    data = [
        {
            'datetime': flow_dt,
            'sortedZoneKeys': sorted_zone_keys,
            'netFlow': flow,
            'source': 'ieso.ca',
        }
        for flow_dt, flow in grouped_dict.items()
    ]

    # being constructed from a dict, data is not guaranteed to be in chronological order.
    # sort it for clean-ness and easier debugging.
    data = sorted(data, key=lambda dp: dp['datetime'])

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    now = arrow.utcnow()

    print('fetch_production() ->')
    print(fetch_production())

    print('we expect correct results when time in UTC and Ontario differs')
    print('data should be for {}'.format(now.replace(hour=2).to(tz_obj).format('YYYY-MM-DD')))
    print('fetch_production("CA-ON", target_datetime=now.replace(hour=2)) ->')
    print(fetch_production("CA-ON", target_datetime=now.replace(hour=2)))

    print('we expect results for 2 months ago')
    print('fetch_production(target_datetime=now.shift(months=-2).datetime)) ->')
    print(fetch_production(target_datetime=now.shift(months=-2).datetime))

    print('there are likely no results for 2 years ago')
    print('fetch_production(target_datetime=now.shift(years=-2).datetime)) ->')
    print(fetch_production(target_datetime=now.shift(years=-2).datetime))

    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange("CA-ON", "US-NY") ->')
    print(fetch_exchange("CA-ON", "US-NY"))

    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.datetime))

    print('test Ontario-to-Manitoba, this must be opposite sign from reported IESO values')
    print('fetch_exchange("CA-ON", "CA-MB", target_datetime=now.datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-MB", target_datetime=now.datetime))

    print('we expect correct results when time in UTC and Ontario differs')
    print('data should be for {}'.format(now.replace(hour=2).to(tz_obj).format('YYYY-MM-DD')))
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.replace(hour=2)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.replace(hour=2)))

    print('we expect results for 2 months ago')
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(months=-2).datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(months=-2).datetime))

    print('there are likely no results for 2 years ago')
    print('fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(years=-2).datetime)) ->')
    print(fetch_exchange("CA-ON", "CA-QC", target_datetime=now.shift(years=-2).datetime))

    print('requesting an exchange with Nova Scotia should raise exception')
    print('fetch_exchange("CA-ON", "CA-NS")) ->')
    print(fetch_exchange("CA-ON", "CA-NS"))
