#!/usr/bin/env python3

"""Parser for the electricity grid of Iraq"""

import arrow
import logging
from dateutil.tz import tz
import requests


LIVE_PRODUCTION_API_URL = "https://www.gdoco.org/vueips.php"
DATA_SOURCE = "www.gdoco.org"
CELL_MAPPING = {
    "hydro": ["1220"],
    "gas": ["1219"],
    "oil": [
        "1218", # Thermal
        "1221" # Diesel
    ],
}


def template_response(zone_key, datetime, source):
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": {
            "gas": 0.0,
            "hydro": 0.0,
            "oil": 0.0,
            "solar": None, # IEA has a count, but no data is available
        },
        "storage": {},
        "source": source,
    }

def fetch_data(r):
    resp = r.get(LIVE_PRODUCTION_API_URL)
    data = resp.json()

    timestamp = arrow.get(data["lastmodified"], "HH:mm:ss A DD-MM-YYYY", tzinfo=tz.gettz('Asia/Baghdad'))

    return data["d"], timestamp.datetime

def fetch_production(
    zone_key=None,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    """Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day, a string in the form YYYYMMDD
    logger (optional) -- handles logging when parser is run
    Return:
    A list of dictionaries in the form:
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
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    data, timestamp = fetch_data(r)

    result = template_response(zone_key, timestamp, DATA_SOURCE)

    for production_type, ids in CELL_MAPPING.items():
        for id in ids:
            result["production"][production_type] += data["d_" + id]

    return [result]


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):

    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    data, timestamp = fetch_data(r)

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))

    if sortedZoneKeys == 'IQ->IR':
        netflow = -1 * (data['d_1226'] +
                        data['d_1227'] +
                        data['d_1228'] +
                        data['d_1229']
                        )
    elif sortedZoneKeys == 'IQ->IQ-KUR':
        netflow = -1 * data['d_1230']
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    exchange = {
        'sortedZoneKeys': sortedZoneKeys,
        'datetime': timestamp,
        'netFlow': netflow,
        'source': DATA_SOURCE
    }

    return exchange

def fetch_consumption(zone_key = 'IQ', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()

    data, timestamp = fetch_data(r)

    consumption = {
            'zoneKey': zone_key,
            'datetime': timestamp,
            'consumption': data['d_1234'],
            'source': DATA_SOURCE
            }

    return consumption


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    r = requests.session()
    print(fetch_production(session=r))
    # print(fetch_production(target_datetime=arrow.get("20200220", "YYYYMMDD")))
    print(fetch_exchange('IQ', 'IR', session=r))
    print(fetch_exchange('IQ', 'IQ-KUR', session=r))
    print(fetch_consumption(session=r))
