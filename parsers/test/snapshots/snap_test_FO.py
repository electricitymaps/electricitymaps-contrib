# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_fetch_production_live[FO-MI] 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-05-06T08:17:00+01:00",
        "production": {
            "biomass": 0.75,
            "hydro": 6.24,
            "oil": 35.19,
            "unknown": 0.0,
            "wind": 7.35,
        },
        "source": "sev.fo",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "FO-MI",
    }
]

snapshots["test_fetch_production_live[FO-SI] 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-05-06T08:17:00+01:00",
        "production": {"hydro": 0.0, "oil": 3.09, "solar": 0.01, "wind": 0.64},
        "source": "sev.fo",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "FO-SI",
    }
]

snapshots["test_fetch_production_live[FO] 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-05-06T08:17:00+01:00",
        "production": {
            "biomass": 0.75,
            "hydro": 6.24,
            "oil": 38.28,
            "solar": 0.01,
            "unknown": 0.0,
            "wind": 7.99,
        },
        "source": "sev.fo",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "FO",
    }
]
