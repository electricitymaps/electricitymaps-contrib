#!/usr/bin/env python3
"""Parser for U.S. Energy Information Administration, https://www.eia.gov/ .

Aggregates and standardizes data from most of the US ISOs,
and exposes them via a unified API.

Requires an API key, set in the EIA_KEY environment variable. Get one here:
https://www.eia.gov/opendata/register.php
"""
import datetime
import os

import arrow
from dateutil import parser
os.environ.setdefault('EIA_KEY', 'eia_key')
from eiapy import Series
import requests

from .ENTSOE import merge_production_outputs

EXCHANGES = {
    'MX-BC->US-CA': 'EBA.CISO-CFE.ID.H',
    'US-BPA->US-IPC': 'EBA.BPAT-IPCO.ID.H',
    'US-SPP->US-TX': 'SWPP.ID.H-EBA.ERCO',
    'US-MISO->US-PJM': 'EBA.MISO-PJM.ID.H',
    'US-MISO->US-SPP': 'EBA.MISO-SWPP.ID.H',
    'US-NEISO->US-NY': 'EBA.ISNE-NYIS.ID.H',
    'US-NY->US-PJM': 'EBA.NYIS-PJM.ID.H'
}
# based on https://www.eia.gov/beta/electricity/gridmonitor/dashboard/electric_overview/US48/US48
REGIONS = {
    'US-CA': 'CAL',
    'US-CAR': 'CAR',
    'US-SPP': 'CENT',
    'US-FL': 'FLA',
    'US-PJM': 'MIDA',
    'US-MISO': 'MIDW',
    'US-NEISO': 'NE',
    'US-NY': 'NY',
    'US-NW': 'NW',
    'US-SE': 'SE',
    'US-SEC': 'SEC',
    'US-SVERI': 'SW',
    'US-TN': 'TEN',
    'US-TX': 'TEX',
}
TYPES = {
    # 'biomass': 'BM',  # not currently supported
    'coal': 'COL',
    'gas': 'NG',
    'hydro': 'WAT',
    'nuclear': 'NUC',
    'oil': 'OIL',
    'unknown': 'OTH',
    'solar': 'SUN',
    'wind': 'WND',
}
PRODUCTION_SERIES = 'EBA.%s-ALL.NG.H'
PRODUCTION_MIX_SERIES = 'EBA.%s-ALL.NG.%s.H'
DEMAND_SERIES = 'EBA.%s-ALL.D.H'
FORECAST_SERIES = 'EBA.%s-ALL.DF.H'


def fetch_consumption_forecast(zone_key, session=None, target_datetime=None, logger=None):
    return _fetch_series(zone_key, FORECAST_SERIES % REGIONS[zone_key],
                         session=session, target_datetime=target_datetime,
                         logger=logger)


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    return _fetch_series(zone_key, PRODUCTION_SERIES % REGIONS[zone_key],
                         session=session, target_datetime=target_datetime,
                         logger=logger)


def fetch_consumption(zone_key, session=None, target_datetime=None, logger=None):
    consumption = _fetch_series(zone_key, DEMAND_SERIES % REGIONS[zone_key],
                                session=session, target_datetime=target_datetime,
                                logger=logger)
    for point in consumption:
        point['consumption'] = point.pop('value')

    return consumption


def fetch_production_mix(zone_key, session=None, target_datetime=None, logger=None):
    mixes = []
    for type, code in TYPES.items():
        series = PRODUCTION_MIX_SERIES % (REGIONS[zone_key], code)
        mix = _fetch_series(zone_key, series, session=session,
                            target_datetime=target_datetime, logger=logger)
        if not mix:
            continue
        for point in mix:
            point.update({
                'production': {type: point.pop('value')},
                'storage': {},  # required by merge_production_outputs()
            })
        mixes.append(mix)

    return merge_production_outputs(mixes, zone_key)


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    sortedcodes = '->'.join(sorted([zone_key1, zone_key2]))
    exchange = _fetch_series(sortedcodes, EXCHANGES[sortedcodes], session=session,
                             target_datetime=target_datetime, logger=logger)
    for point in exchange:
        point.update({
            'sortedZoneKeys': point.pop('zoneKey'),
            'netFlow': point.pop('value'),
        })
        if sortedcodes == 'MX-BC->US-CA':
            point['netFlow'] = -point['netFlow']

    return exchange


def _fetch_series(zone_key, series_id, session=None, target_datetime=None,
                  logger=None):
    """Fetches and converts a data series."""
    s = session or requests.Session()
    series = Series(series_id=series_id, session=s)

    if target_datetime:
        raw_data = series.last_from(24, end=target_datetime)
    else:
        # Get the last 24 hours available.
        raw_data = series.last(24)

    # UTC timestamp with no offset returned.
    if not raw_data.get('series'):
        # Series doesn't exist. Probably requesting a fuel from a region that
        # doesn't have any capacity for that fuel type.
        return []

    return [{
        'zoneKey': zone_key,
        'datetime': parser.parse(datapoint[0]),
        'value': datapoint[1],
        'source': 'eia.gov',
    } for datapoint in raw_data['series'][0]['data']]


def main():
    "Main method, never used by the Electricity Map backend, but handy for testing."
    from pprint import pprint
    pprint(fetch_consumption_forecast('US-NY'))
    pprint(fetch_production('US-SEC'))
    pprint(fetch_production_mix('US-CAR'))
    pprint(fetch_consumption('US-CAR'))
    pprint(fetch_exchange('MX-BC', 'US-CA'))


if __name__ == '__main__':
    main()
