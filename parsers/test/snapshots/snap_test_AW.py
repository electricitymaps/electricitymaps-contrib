# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestWebaruba::test_fetch_production 1"] = [
    {
        "datetime": "2023-09-12T03:45:02.384000-04:00",
        "production": {
            "biomass": 0.0,
            "oil": 108.567078,
            "solar": 0.0,
            "unknown": 0,
            "wind": 4.692129,
        },
        "source": "webaruba.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AW",
    }
]
