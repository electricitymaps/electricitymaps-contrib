#!/usr/bin/env python3
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

exchanges_mapping = {
    'BY->LT': [
        'BY->LT'
    ],
    'DE->DK': [
        'DE->DK1',
        'DE->DK2'
    ],
    'DE->SE': [
        'DE->SE4'
    ],
    'DK->NO': [
        'DK1->NO2'
    ],
    'DK->SE': [
        'DK1->SE3',
        'DK2->SE4'
    ],
    'EE->RU': [
        'EE->RU'
    ],
    'EE->LV': [
        'EE->LV'
    ],
    'EE->FI': [
        'EE->FI'
    ],
    'FI->NO': [
        'FI->NO4'
    ],
    'FI->RU': [
        'FI->RU'
    ],
    'FI->SE': [
        'FI->SE1',
        'FI->SE3'
    ],
    'LT->LV': [
        'LT->LV'
    ],
    'LT->SE': [
        'LT->SE4'
    ],
    'LT->PL': [
        'LT->PL'
    ],
    'LT->RU-KGD': [
        'LT->RU'
    ],
    'LV->RU': [
        'LV->RU'
    ],
    'NL->NO': [
        'NL->NO2'
    ],
    'NO->SE': [
        'NO1->SE3',
        'NO3->SE2',
        'NO4->SE1',
        'NO4->SE2'
    ],
    'NO->RU': [
        'NO4->RU'
    ],
    'PL->SE': [
        'PL->SE4'
    ]
}

def fetch_production(country_code='SE', session=None):
    r = session or requests.session()
    timestamp = arrow.now().timestamp * 1000
    url = 'http://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview?timestamp=%d' % timestamp
    response = r.get(url)
    obj = response.json()

    data = {
        'countryCode': country_code,
        'production': {
            'nuclear': float(list(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Nuclear', country_code),
                obj['NuclearData']))[0]['value'].replace(u'\xa0', '')),
            'hydro': float(list(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Hydro', country_code),
                obj['HydroData']))[0]['value'].replace(u'\xa0', '')),
            'wind': float(list(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Wind', country_code),
                obj['WindData']))[0]['value'].replace(u'\xa0', '')),
            'unknown':
                float(list(filter(
                    lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Thermal', country_code),
                    obj['ThermalData']))[0]['value'].replace(u'\xa0', '')) +
                float(list(filter(
                    lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('NotSpecified', country_code),
                    obj['NotSpecifiedData']))[0]['value'].replace(u'\xa0', '')),
        },
        'storage': {},
        'source': 'driftsdata.stattnet.no',
    }
    data['datetime'] = arrow.get(obj['MeasuredAt'] / 1000).datetime

    return data

def fetch_exchange_by_bidding_zone(bidding_zone1='DK1', bidding_zone2='NO2', session=None):
    bidding_zone_a, bidding_zone_b = sorted([bidding_zone1, bidding_zone2])
    r = session or requests.session()
    timestamp = arrow.now().timestamp * 1000
    url = 'http://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow?Ticks=%d' % timestamp
    response = r.get(url)
    obj = response.json()

    exchange = list(filter(
        lambda x: set([x['OutAreaElspotId'], x['InAreaElspotId']]) == set([bidding_zone_a, bidding_zone_b]),
        obj))[0]

    return {
        'sortedBiddingZones': '->'.join([bidding_zone_a, bidding_zone_b]),
        'netFlow': exchange['Value'] if bidding_zone_a == exchange['OutAreaElspotId'] else -1 * exchange['Value'],
        'datetime': arrow.get(obj[0]['MeasureDate'] / 1000).datetime,
        'source': 'driftsdata.stattnet.no',
    }

def _fetch_exchanges_from_sorted_bidding_zones(sorted_bidding_zones, session=None):
    zones = sorted_bidding_zones.split('->')
    return fetch_exchange_by_bidding_zone(zones[0], zones[1], session)

def _sum_of_exchanges(exchanges):
    exchange_list = list(exchanges)
    return {
        'netFlow': sum(e['netFlow'] for e in exchange_list),
        'datetime': exchange_list[0]['datetime'],
        'source': exchange_list[0]['source']
    }

def fetch_exchange(country_code1='DK', country_code2='NO', session=None):
    r = session or requests.session()

    sorted_exchange = '->'.join(sorted([country_code1, country_code2]))
    data = _sum_of_exchanges(map(lambda e: _fetch_exchanges_from_sorted_bidding_zones(e, r),
        exchanges_mapping[sorted_exchange]))
    data['sortedCountryCodes'] = '->'.join(sorted([country_code1, country_code2]))

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production(SE) ->')
    print(fetch_production('SE'))
    print('fetch_exchange(NO, SE) ->')
    print(fetch_exchange('NO', 'SE'))
