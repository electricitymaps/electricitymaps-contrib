# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestCNDC::test_fetch_generation_forecast 1'] = [
    {
        'datetime': '2023-12-20T00:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1199.23,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T01:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1141.49,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T02:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1108.31,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T03:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1088.02,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T04:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1118.32,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T05:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1080.45,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T06:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1228.59,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T07:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1292.94,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T08:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1399.9,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T09:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1454.64,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T10:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1485.06,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T11:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1499.31,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T12:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1488.93,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T13:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1547.23,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T14:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1590.45,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T15:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1572.62,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T16:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1516.26,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T17:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1442.56,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T18:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1571.34,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T19:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1627.02,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T20:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1599.87,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T21:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1525.8,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T22:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1411.17,
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T23:00:00-04:00',
        'source': 'cndc.bo',
        'value': 1294.64,
        'zoneKey': 'BO'
    }
]

snapshots['TestCNDC::test_fetch_production 1'] = [
    {
        'datetime': '2023-12-20T00:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 384.86,
            'solar': 0,
            'unknown': 744.75,
            'wind': 45.39
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T01:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 402.78,
            'solar': 0,
            'unknown': 696.4,
            'wind': 47.16
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T02:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 406.37,
            'solar': 0,
            'unknown': 661.4,
            'wind': 48.76
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T03:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 380.18,
            'solar': 0,
            'unknown': 662.76,
            'wind': 47.33
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T04:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 379.26,
            'solar': 0,
            'unknown': 661.1500000000001,
            'wind': 51.32
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T05:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 350.42,
            'solar': 0.39,
            'unknown': 647.5,
            'wind': 50.26
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T06:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 422.66,
            'solar': 13.45,
            'unknown': 670.38,
            'wind': 41.49
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T07:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 500.35,
            'solar': 47.85,
            'unknown': 717.29,
            'wind': 45.95
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T08:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 505.62,
            'solar': 90.01,
            'unknown': 769.71,
            'wind': 46.62
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T09:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 523.88,
            'solar': 113.07,
            'unknown': 845.1199999999999,
            'wind': 32.52
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    },
    {
        'datetime': '2023-12-20T10:00:00-04:00',
        'production': {
            'biomass': 0,
            'hydro': 511.72,
            'solar': 124.97,
            'unknown': 920.99,
            'wind': 24.76
        },
        'source': 'cndc.bo',
        'storage': {
        },
        'zoneKey': 'BO'
    }
]
