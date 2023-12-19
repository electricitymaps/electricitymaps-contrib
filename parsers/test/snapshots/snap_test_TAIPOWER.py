# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_production 1"] = [
    {
        "capacity": {
            "biomass": 38.2,
            "coal": 14697.2,
            "gas": 18060.6,
            "geothermal": 7.2,
            "hydro": 2101.9999999999995,
            "nuclear": 1902.0,
            "oil": 1592.5,
            "solar": 10822.4,
            "unknown": 626.9,
            "wind": 958.0,
        },
        "datetime": "2023-09-24T01:30:00+08:00",
        "production": {
            "biomass": 25.3,
            "coal": 12710.3,
            "gas": 12226.0,
            "geothermal": 2.7,
            "hydro": 459.6,
            "nuclear": 1877.4,
            "oil": 364.6,
            "solar": 0.0,
            "unknown": 617.4,
            "wind": 29.4,
        },
        "source": "taipower.com.tw",
        "sourceType": "measured",
        "storage": {"hydro": 245.8},
        "zoneKey": "TW",
    }
]
