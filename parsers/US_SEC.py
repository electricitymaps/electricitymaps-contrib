#!/usr/bin/env python3

"""
Parser for the Seminole Electric Cooperative in Florida, USA.

Combines hourly gas and coal production data from EIA with hourly solar generation from http://apps.seminole.coop/db/cs/ . Both generally lag a day or so behind, and sometimes as much as 10d behind.

https://www.seminole-electric.com/facilities/generation/ lists two 650MW coal-fired plants, one 810MW gas plant, and a small 2.2MW solar farm. However, EIA combines coal and gas generation data, so we report those together as unknown.

https://github.com/tmrowco/electricitymap-contrib/issues/1713
"""

import logging
from datetime import timezone

import pandas as pd

from . import EIA
from .ENTSOE import merge_production_outputs


def fetch_production(zone_key='US-SEC', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    unknown = fetch_unknown(zone_key=zone_key, session=session,
                            target_datetime=target_datetime, logger=logger)
    solar = fetch_solar(session=session, logger=logger)
    return merge_production_outputs((unknown, solar), zone_key,
                                    merge_source='eia.org, apps.seminole.coop')


def fetch_unknown(zone_key='US-SEC', session=None, target_datetime=None,
                  logger=logging.getLogger(__name__)):
    data = EIA.fetch_production(zone_key=zone_key, session=session,
                                target_datetime=target_datetime, logger=logger)
    for hour in data:
        hour.update({
            'production': {'unknown': hour.pop('value')},
            'storage': {},  # required by merge_production_outputs
        })

    return data


def fetch_solar(session=None, logger=logging.getLogger(__name__)):
    url = 'http://apps.seminole.coop/db/cs/render.ashx?ItemPath=/Applications/Solar+Dashboard/Cooperative+Solar+-+Data&Format=EXCEL&rptHDInterval=Week&rptHDOffset=0'
    df = pd.read_excel(url, sheet_name='Hourly', skiprows=[0])

    return [{
        'zoneKey': 'US-SEC',
        'datetime': row['Date/Time (UTC)'].to_pydatetime().replace(tzinfo=timezone.utc),
        'production': {'solar': row['kW'] / 1000.0},
        'storage': {},  # required by merge_production_outputs
        'source': 'apps.seminole.coop',
    } for _, row in df.iterrows()]


def main():
    """Main method, not used by the ElectricityMap backend, just for testing."""
    import pprint
    print('fetch_production() ->')
    print(pprint.pprint(fetch_production()))


if __name__ == '__main__':
    main()
