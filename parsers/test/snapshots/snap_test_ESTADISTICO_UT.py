# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestESTADISTICO_UT::test_fetch_production 1'] = [
    {
        'datetime': '2023-12-29T00:00:00-06:00',
        'production': {
            'biomass': 152.46,
            'coal': 0.0,
            'gas': 0.0,
            'geothermal': 169.52,
            'hydro': 102.3,
            'nuclear': 0.0,
            'oil': 313.71,
            'solar': 0.0,
            'unknown': 0.0,
            'wind': 11.09
        },
        'source': 'ut.com.sv',
        'storage': {
            'hydro': None
        },
        'zoneKey': 'SV'
    },
    {
        'datetime': '2023-12-29T01:00:00-06:00',
        'production': {
            'biomass': 153.04,
            'coal': 0.0,
            'gas': 0.0,
            'geothermal': 169.39,
            'hydro': 109.89,
            'nuclear': 0.0,
            'oil': 282.69,
            'solar': 0.0,
            'unknown': 0.0,
            'wind': 5.9
        },
        'source': 'ut.com.sv',
        'storage': {
            'hydro': None
        },
        'zoneKey': 'SV'
    },
    {
        'datetime': '2023-12-29T02:00:00-06:00',
        'production': {
            'biomass': 151.57,
            'coal': 0.0,
            'gas': 0.0,
            'geothermal': 169.64,
            'hydro': 113.99,
            'nuclear': 0.0,
            'oil': 255.78,
            'solar': 0.0,
            'unknown': 0.0,
            'wind': 10.01
        },
        'source': 'ut.com.sv',
        'storage': {
            'hydro': None
        },
        'zoneKey': 'SV'
    }
]
