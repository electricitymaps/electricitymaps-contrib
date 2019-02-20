#!/usr/bin/env python3

from collections import defaultdict
import datetime
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

PRODUCTION_URL = 'http://reports.ieso.ca/public/GenOutputCapability/PUB_GenOutputCapability_{YYYYMMDD}.xml'

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
    filename = dt.format('YYYYMMDD')

    r = session or requests.session()
    url = PRODUCTION_URL.format(YYYYMMDD=filename)
    response = r.get(url)

    if not response.ok:
        # Data is generally available for past 3 months. Requesting files older than this
        # returns an HTTP 404 error.
        logger.info('CA-ON: failed getting requested data for datetime {} from IESO server'.format(dt))
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
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key: used in case a parser is able to fetch multiple zones
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

    dt = arrow.get(target_datetime).to(tz_obj)
    filename = dt.format('YYYYMMDD')

    r = session or requests.session()
    url = 'http://reports.ieso.ca/public/IntertieScheduleFlow/PUB_IntertieScheduleFlow_{}.xml'.format(filename)
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    interties = soup.find_all('intertiezone')

    sought_intertie_flows = defaultdict(list)

    for intertie in interties:
        intertie_name = intertie.find('intertiezonename').text

        if intertie_name not in exchange_maps:
            logger.warning('CA-ON: unrecognized intertie name {}, please implement it!'.format(intertie_name))
            continue

        mapping = exchange_maps[intertie_name]

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

        for actual in actuals:
            hour = int(actual.find('hour').text) - 1
            minute = (int(actual.find('interval').text) - 1) * 5
            flow = float(actual.find('flow').text) * direction

            dt_aware = datetime.datetime(dt.year, dt.month, dt.day, hour, minute, tzinfo=tz_obj)

            sought_intertie_flows[dt_aware].append(flow)

    # add up values for same datetime for exchanges with more than one intertie
    data = [
        {
            'datetime': flow_dt,
            'sortedZoneKeys': sorted_zone_keys,
            'netFlow': sum(flow_figures),
            'source': 'ieso.ca'
        }
        for flow_dt, flow_figures in sought_intertie_flows.items()
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
