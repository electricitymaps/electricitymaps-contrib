#!/usr/bin/env python3

"""Parse Peninsular Malaysian electricity data from the GSO API."""

# The states of Sabah and Sarawak are not included. There is pumped storage on
# the Peninsula but no data is currently available.
# https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

# Standard library imports
import collections
import datetime
import json
import logging

# Third-party library imports
import arrow
import requests

# Local library imports
from parsers.lib import config, validation

DEFAULT_ZONE_KEY = 'MY-WM'
DOMAIN = 'www.gso.org.my'
PRODUCTION_THRESHOLD = 10 # MW
TIMEZONE = 'Asia/Kuala_Lumpur'
URL_FORMAT_STRING = 'https://{}/SystemData/{}/GetChartDataSource'
EXCHANGE_URL = URL_FORMAT_STRING.format(DOMAIN, 'TieLine.aspx')
PRODUCTION_URL = URL_FORMAT_STRING.format(DOMAIN, 'CurrentGen.aspx')


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_exchange(zone_key1,
                   zone_key2,
                   session=None,
                   target_datetime=None,
                   logger=None) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format('DD/MM/YYYY')
    session = session or requests.Session()
    sorted_zone_keys = '->'.join(sorted((zone_key1, zone_key2)))
    if sorted_zone_keys == 'MY-WM->SG':
        # The Singapore exchange is a PLTG tie.
        return [
            {
                'datetime': arrow.get(exchange['Tarikhmasa'], tzinfo=TIMEZONE)
                                 .datetime,
                'netFlow': exchange['MW'],
                'sortedZoneKeys': sorted_zone_keys,
                'source': DOMAIN,
            }
            for exchange in get_api_data(session,
                                         EXCHANGE_URL,
                                         {
                                             'Fromdate': date_string,
                                             'Todate': date_string,
                                             'Line': 'PLTG',
                                         })
        ]
    elif sorted_zone_keys == 'MY-WM->TH':
        # The Thailand exchange is made up of EGAT and HVDC ties.
        egat_exchanges = get_api_data(session,
                                      EXCHANGE_URL,
                                      {
                                          'Fromdate': date_string,
                                          'Todate': date_string,
                                          'Line': 'EGAT',
                                      })
        hvdc_exchanges = get_api_data(session,
                                      EXCHANGE_URL,
                                      {
                                          'Fromdate': date_string,
                                          'Todate': date_string,
                                          'Line': 'HVDC',
                                      })
        exchanges = collections.defaultdict(float)
        for exchange in egat_exchanges + hvdc_exchanges:
            exchanges[exchange['Tarikhmasa']] += exchange['MW']
        return [
            {
                'datetime': arrow.get(timestamp, tzinfo=TIMEZONE).datetime,
                'netFlow': power,
                'sortedZoneKeys': sorted_zone_keys,
                'source': DOMAIN,
            }
            for timestamp, power in exchanges.items()
        ]
    else:
        raise NotImplementedError("'{sorted_zone_keys}' is not implemented")


@config.refetch_frequency(datetime.timedelta(minutes=10))
def fetch_production(zone_key=DEFAULT_ZONE_KEY,
                     session=None,
                     target_datetime=None,
                     logger=logging.getLogger(__name__)) -> list:
    """Requests the last known production mix (in MW) of a given zone."""
    date_string = arrow.get(target_datetime).to(TIMEZONE).format('DD/MM/YYYY')
    return [
        validation.validate(
            {
                'datetime': arrow.get(breakdown['DT'], tzinfo=TIMEZONE)
                                 .datetime,
                'production': {
                    'coal': breakdown['Coal'],
                    'gas': breakdown['Gas'],
                    'hydro': breakdown['Hydro'],
                    'oil': breakdown['Oil'],
                    'solar': breakdown['Solar'],
                    'unknown': breakdown['CoGen'],
                },
                'source': DOMAIN,
                'zoneKey': zone_key,
            },
            logger,
            floor=PRODUCTION_THRESHOLD,
            remove_negative=True)
        for breakdown in get_api_data(session or requests.Session(),
                                      PRODUCTION_URL,
                                      {
                                          'Fromdate': date_string,
                                          'Todate': date_string,
                                      })
    ]


def get_api_data(session, url, data):
    """Parse JSON data from the API."""
    # The API returns a JSON string containing only one key-value pair whose
    # value is another JSON string. We must therefore parse the response as
    # JSON, access the lone value, and parse it as JSON again!
    return json.loads(session.post(url, json=data).json()['d'])


if __name__ == '__main__':
    # Never used by the electricityMap back-end, but handy for testing.
    print('fetch_production():')
    print(fetch_production())
    print('fetch_exchange(MY-WM, SG):')
    print(fetch_exchange('MY-WM', 'SG'))
    print('fetch_exchange(MY-WM, TH):')
    print(fetch_exchange('MY-WM', 'TH'))
