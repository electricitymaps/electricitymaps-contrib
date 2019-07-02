#!/usr/bin/env python3

"""Parser for the Seminole Electric Cooperative in Florida, USA.

https://github.com/tmrowco/electricitymap-contrib/issues/1713
"""

import logging
from datetime import timezone

import pandas as pd


def fetch_solar(session=None, logger=logging.getLogger(__name__)):
    url = 'http://apps.seminole.coop/db/cs/render.ashx?ItemPath=/Applications/Solar+Dashboard/Cooperative+Solar+-+Data&Format=EXCEL&rptHDInterval=Day&rptHDOffset=0'
    df = pd.read_excel(url, sheet_name='Hourly', skiprows=[0])

    return [{
        'zoneKey': 'US_SEC',
        'datetime': row['Date/Time (UTC)'].to_pydatetime().replace(tzinfo=timezone.utc),
        'production': {'solar': row['kW'] / 1000.0},
        'source': 'apps.seminole.coop',
    } for _, row in df.iterrows()]



if __name__ == '__main__':
    """Main method, not used by the ElectricityMap backend, just for testing."""

    import json, pprint
    print('fetch_solar() ->')
    print(pprint.pprint(fetch_solar()))
