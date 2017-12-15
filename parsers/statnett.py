# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

exchanges_mapping = {
    'DE->SE': [
        'DE->SE4'
    ],
    'DK->SE': [
        'DK1->SE3',
        'DK2->SE4'
    ],
    'FI->SE': [
        'FI->SE1',
        'FI->SE3'
    ],
    'LT->SE': [
        'LT->SE4'
    ],
    'NO->SE': [
        'NO1->SE3',
        'NO3->SE2',
        'NO4->SE1',
        'NO4->SE2'
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
            'nuclear': float(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Nuclear', country_code),
                obj['NuclearData'])[0]['value'].replace(u'\xa0', '')),
            'hydro': float(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Hydro', country_code),
                obj['HydroData'])[0]['value'].replace(u'\xa0', '')),
            'wind': float(filter(
                lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Wind', country_code),
                obj['WindData'])[0]['value'].replace(u'\xa0', '')),
            'unknown':
                float(filter(
                    lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('Thermal', country_code),
                    obj['ThermalData'])[0]['value'].replace(u'\xa0', '')) +
                float(filter(
                    lambda x: x['titleTranslationId'] == 'ProductionConsumption.%s%sDesc' % ('NotSpecified', country_code),
                    obj['NotSpecifiedData'])[0]['value'].replace(u'\xa0', '')),
        },
        'storage': {},
        'source': 'driftsdata.stattnet.no',
    }
    data['datetime'] = arrow.get(obj['MeasuredAt'] / 1000).datetime

    return data

def fetch_exchange_by_bidding_zone(bidding_zone1='NO1', bidding_zone2='SE3', session=None):
    r = session or requests.session()
    timestamp = arrow.now().timestamp * 1000
    url = 'http://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow?Ticks=%d' % timestamp
    response = r.get(url)
    obj = response.json()

    net_flow = filter(
        lambda x: x['OutAreaElspotId'] == bidding_zone1 and x['InAreaElspotId'] == bidding_zone2,
        obj)[0]['Value']

    return {
        'sortedBiddingZones': '->'.join(sorted([bidding_zone1, bidding_zone2])),
        'netFlow': net_flow if bidding_zone1 == sorted([bidding_zone1, bidding_zone2])[0] else -1 * net_flow,
        'datetime': arrow.get(obj[0]['MeasureDate'] / 1000).datetime,
        'source': 'driftsdata.stattnet.no',
    }

def _fetch_exchanges_from_sorted_bidding_zones(sorted_bidding_zones, session=None):
    zones = sorted_bidding_zones.split('->')
    return fetch_exchange_by_bidding_zone(zones[0], zones[1], session)

def _sum_of_exchanges(exchanges):
    return {
        'netFlow': sum(map(lambda e: e['netFlow'], exchanges)),
        'datetime': exchanges[0]['datetime'],
        'source': exchanges[0]['source']
    }

def fetch_exchange(country_code1='NO', country_code2='SE', session=None):
    r = session or requests.session()

    sorted_exchange = '->'.join(sorted([country_code1, country_code2]))
    data = _sum_of_exchanges(map(lambda e: _fetch_exchanges_from_sorted_bidding_zones(e, r),
        exchanges_mapping[sorted_exchange]))
    data['sortedCountryCodes'] = '->'.join(sorted([country_code1, country_code2]))

    return data

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production(SE) ->'
    print fetch_production('SE')
    print 'fetch_exchange(NO, SE) ->'
    print fetch_exchange('NO', 'SE')
