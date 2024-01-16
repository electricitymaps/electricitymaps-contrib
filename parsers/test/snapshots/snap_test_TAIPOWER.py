# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_production 1"] = [
    {
        "capacity": {
            "biomass": 38.2,
            "coal": 14197.2,
            "gas": 18060.6,
            "geothermal": 7.2,
            "hydro": 2101.9999999999995,
            "nuclear": 1902.0,
            "oil": 1592.5,
            "solar": 11304.099999999999,
            "unknown": 626.9,
            "wind": 1032.4,
        },
        "datetime": "2023-12-29T19:10:00+08:00",
        "production": {
            "biomass": 25.8,
            "coal": 6367.6,
            "gas": 14010.6,
            "geothermal": 2.6,
            "hydro": 458.7,
            "nuclear": 1894.4,
            "oil": 314.5,
            "solar": 0.0,
            "unknown": 1494.6,
            "wind": 1712.7,
        },
        "source": "taipower.com.tw",
        "sourceType": "measured",
        "storage": {"hydro": -935.7},
        "zoneKey": "TW",
    }
]
