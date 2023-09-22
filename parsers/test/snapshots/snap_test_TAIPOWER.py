# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_production 1"] = [
    {
        "capacity": {
            "biomass": 38.2,
            "coal": 14697.2,
            "gas": 18060.6,
            "geothermal": 0.0,
            "hydro": 2101.9999999999995,
            "nuclear": 1902.0,
            "oil": 1592.5,
            "solar": 10822.4,
            "unknown": 626.9,
            "wind": 958.0,
        },
        "datetime": "2023-09-22T21:50:00+08:00",
        "production": {
            "biomass": 12.5,
            "coal": 12956.6,
            "gas": 14129.4,
            "geothermal": 0.0,
            "hydro": 673.5,
            "nuclear": 1884.2,
            "oil": 375.7,
            "solar": 0.0,
            "unknown": 1660.7,
            "wind": 743.7,
        },
        "source": "taipower.com.tw",
        "sourceType": "measured",
        "storage": {"hydro": -645.9},
        "zoneKey": "TW",
    }
]
