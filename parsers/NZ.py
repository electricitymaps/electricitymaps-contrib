#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import json
from bs4 import BeautifulSoup

timezone = 'Pacific/Auckland'

NZ_NZN_PRICE_REGIONS = set(['region{}'.format(i) for i in range(1, 9)])
NZ_NZS_PRICE_REGIONS = set(['region{}'.format(i) for i in range(9, 14)])
NZ_PRICE_REGIONS = set(['region{}'.format(i) for i in range(1, 14)])

def fetch(session=None):
    r = session or requests.session()
    url = 'https://www.transpower.co.nz/power-system-live-data'
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for item in soup.find_all('script'):
        if 'src' in item.attrs:
            continue
        body = item.contents[0]
        if not body.startswith('jQuery.extend(Drupal.settings'):
            continue
        obj = json.loads(body.replace('jQuery.extend(Drupal.settings, ', '').replace(');', ''))
        break
    return obj

def fetch_price(zone_key='NZ-NZN', session=None, target_datetime=None, logger=None) -> dict:
    """
    Requests the current price of electricity based on the zone key.

    Note that since EM6 breaks the electricity price down into regions while electricitymap breaks
    it down into the North and South islands, the regions are averaged out for each island.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not able to retrieve data for past dates')

    r = session or requests.session()
    url = 'https://em6live.co.nz'
    response = r.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    prices = soup.find(id='priceList')
    region_prices = []

    if zone_key == 'NZ-NZN':
        regions = NZ_NZN_PRICE_REGIONS
    elif zone_key == 'NZ-NZS':
        regions = NZ_NZS_PRICE_REGIONS
    elif zone_key == 'NZ':
        regions = NZ_PRICE_REGIONS
    else:
        raise NotImplementedError('Unsupported zone_key %s' % zone_key)
    
    for item in prices.find_all('li'):
        region = item['id']
        if region in regions:
            price = float(item.get_text().replace('$', '').replace(',', ''))
            region_prices.append(price)

    avg_price = sum(region_prices) / len(region_prices)
    time = soup.find(id='overviewPrice').find(class_='updateStamp')
    datetime = arrow.get(time.get_text(), 'DD/MM/YY HH:mm', tzinfo='Pacific/Auckland')

    return {
        'datetime': datetime.datetime,
        'price': avg_price,
        'currency': 'NZD',
        'source': 'em6live.co.nz',
        'zoneKey': zone_key
    }

def fetch_production(zone_key='NZ', session=None, target_datetime=None, logger=None) -> dict:
    """Requests the last known production mix (in MW) of a given zone."""
    if target_datetime:
        raise NotImplementedError('This parser is not able to retrieve data for past dates')

    obj = fetch(session)

    datetime = arrow.get(obj['soPgenGraph']['timestamp'],"X").datetime

    if zone_key == 'NZ-NZN':
        region_key = 'North Island'
    elif zone_key == 'NZ-NZS':
        region_key = 'South Island'
    elif zone_key == 'NZ':
        region_key = 'New Zealand'
    else:
        raise NotImplementedError('Unsupported zone_key %s' % zone_key)

    productions = obj['soPgenGraph']['data'][region_key]

    data = {
        'zoneKey': zone_key,
        'datetime': datetime,
        'production': {
            'coal': productions.get('Coal', {'generation': 0.0})['generation'],
            'oil': productions.get('Liquid', {'generation': 0.0})['generation'],
            'gas': productions.get('Gas', {'generation': 0.0})['generation'],
            'geothermal': productions.get('Geothermal', {'generation': 0.0})['generation'],
            'wind': productions.get('Wind', {'generation': 0.0})['generation'],
            'hydro': productions.get('Hydro', {'generation': 0.0})['generation'],
            'unknown': productions.get('Co-Gen', {'generation': 0.0})['generation'],
            'nuclear': 0  # famous issue in NZ politics
        },
        'capacity': {
            'coal': productions.get('Coal', {'capacity': 0.0})['capacity'],
            'oil': productions.get('Liquid', {'capacity': 0.0})['capacity'],
            'gas': productions.get('Gas', {'capacity': 0.0})['capacity'],
            'geothermal': productions.get('Geothermal', {'capacity': 0.0})['capacity'],
            'wind': productions.get('Wind', {'capacity': 0.0})['capacity'],
            'hydro': productions.get('Hydro', {'capacity': 0.0})['capacity'],
            'battery storage': productions.get('Battery', {'capacity': 0.0})['capacity'],
            'unknown': productions.get('Co-Gen', {'capacity': 0.0})['capacity'],
            'nuclear': 0  # famous issue in NZ politics
        },
        'storage': {
            'battery': productions.get('Battery', {'generation': 0.0})['generation'],
        },
        'source': 'transpower.co.nz',
    }

    return data


def fetch_exchange(zone_key1='NZ-NZN', zone_key2='NZ-NZS', session=None, target_datetime=None,
                   logger=None) -> list:
    """Requests the last known power exchange (in MW) between New Zealand's two islands."""
    if target_datetime:
        raise NotImplementedError('This parser is not able to retrieve data for past dates')

    obj = fetch(session)['soHVDCDailyGraph']
    datetime_start = arrow.now().to(timezone).floor('day')
    data = []
    for item in obj['data']['mw_north']:
        datetime = datetime_start.shift(minutes=+item[0])
        if datetime > arrow.get() or item[1] is None:
            continue
        netFlow = item[1]
        data.append({
            'sortedZoneKeys': 'NZ-NZN->NZ-NZS',
            'datetime': datetime.datetime,
            'netFlow': -1 * netFlow,
            'source': 'transpower.co.nz'
        })

    return data

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_price(NZ-NZN) ->')
    print(fetch_price('NZ-NZN'))
    print('fetch_price(NZ-NZS) ->')
    print(fetch_price('NZ-NZS'))
    print('fetch_production(NZ-NZN) ->')
    print(fetch_production('NZ-NZN'))
    print('fetch_production(NZ-NZS) ->')
    print(fetch_production('NZ-NZS'))
    print('fetch_production(NZ) ->')
    print(fetch_production('NZ'))
    print('fetch_exchange() ->')
    print(fetch_exchange())
