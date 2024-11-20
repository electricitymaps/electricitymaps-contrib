# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestPA::test_fetch_production 1"] = [
    {
        "correctedModes": [],
        "datetime": "2021-12-30T09:58:37-05:00",
        "production": {
            "biomass": 2.75,
            "coal": 149.6,
            "gas": 355.88,
            "hydro": 421.84,
            "oil": 238.2,
            "solar": 262.76,
            "unknown": 0.0,
            "wind": 115.4,
        },
        "source": "sitr.cnd.com.pa",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "PA",
    }
]
