# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestBG::test_fetch_production 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-01-01T12:00:00+00:00",
        "production": {
            "biomass": 21.58,
            "coal": 762.85,
            "gas": 458.2,
            "hydro": 778.79,
            "nuclear": 2118.06,
            "solar": 159.23,
            "wind": 178.62,
        },
        "source": "eso.bg",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "BG",
    }
]
