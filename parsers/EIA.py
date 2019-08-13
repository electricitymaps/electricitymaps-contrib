#!/usr/bin/env python3

import os

import arrow
from dateutil import parser
os.environ.setdefault('EIA_KEY', 'eia_key')
from eiapy import Series
import requests

DAY_AHEAD = {
    'US-SPP': 'EBA.SWPP-ALL.DF.H',
    'US-MISO': 'EBA.MISO-ALL.DF.H',
    'US-CA': 'EBA.CAL-ALL.DF.H',
    'US-NEISO': 'EBA.ISNE-ALL.DF.H',
    'US-NY': 'EBA.NYIS-ALL.DF.H',
    'US-PJM': 'EBA.PJM-ALL.DF.H',
    'US-BPA': 'EBA.BPAT-ALL.DF.H',
    'US-IPC': 'EBA.IPCO-ALL.DF.H'
}

PRODUCTION = {
    'US-SC': 'EBA.SC-ALL.NG.H',
    'US-SCEG': 'EBA.SCEG-ALL.NG.H',
    'US-SEC': 'EBA.SEC-ALL.NG.H',
}

EXCHANGES = {
    'MX-BC->US-CA': 'EBA.CISO-CFE.ID.H',
    'US-BPA->US-IPC': 'EBA.BPAT-IPCO.ID.H',
    'US-SPP->US-TX': 'SWPP.ID.H-EBA.ERCO',
    'US-MISO->US-PJM': 'EBA.MISO-PJM.ID.H',
    'US-MISO->US-SPP': 'EBA.MISO-SWPP.ID.H',
    'US-NEISO->US-NY': 'EBA.ISNE-NYIS.ID.H',
    'US-NY->US-PJM': 'EBA.NYIS-PJM.ID.H'
}


def fetch_consumption_forecast(zone_key, session=None, target_datetime=None,
                               logger=None):
    return _fetch_production_or_consumption(
        zone_key, DAY_AHEAD[zone_key], session=session,
        target_datetime=target_datetime, logger=logger)


def fetch_production(zone_key, session=None, target_datetime=None,
                     logger=None):
    return _fetch_production_or_consumption(
        zone_key, PRODUCTION[zone_key], session=session,
        target_datetime=target_datetime, logger=logger)


def _fetch_production_or_consumption(zone_key, series_id, session=None,
                                     target_datetime=None, logger=None):
    """Fetches production or consumption forecast, determined by series_id."""
    s = session or requests.Session()
    series = Series(series_id=series_id, session=s)

    if target_datetime:
        raw_data = series.last_from(24, end=target_datetime)
    else:
        # Get the last 24 hours available.
        raw_data = series.last(24)

    # UTC timestamp with no offset returned.

    return [{
        'zoneKey': zone_key,
        'datetime': parser.parse(datapoint[0]),
        'value': datapoint[1],
        'source': 'eia.org',
    } for datapoint in raw_data['series'][0]['data']]


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    zone_key1           -- the first country code
    zone_key2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime (optional)      -- string in form YYYYMMDDTHHZ
    Return:
    A list of dictionaries in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))

    series_id = EXCHANGES[sortedcodes]
    s = session or requests.Session()
    exchange_series = Series(series_id=series_id, session=s)

    if target_datetime:
        raw_data = exchange_series.last_from(24, end=target_datetime)
    else:
        # Get the last 24 hours available.
        raw_data = exchange_series.last(24)['series'][0]['data']

    data = []
    for datapoint in raw_data:
        if sortedcodes == 'MX-BC->US-CA':
            datapoint[1] = -1*datapoint[1]

        exchange = {'sortedZoneKeys': sortedcodes,
                    'datetime': parser.parse(datapoint[0]),
                    'netFlow': datapoint[1],
                    'source': 'mysource.com'}

        data.append(exchange)

    return data


if __name__ == '__main__':
    "Main method, never used by the Electricity Map backend, but handy for testing."

    print(fetch_consumption_forecast('US-NY'))
    print(fetch_production('US-SEC'))
    print(fetch_exchange('MX-BC', 'US-CA'))
