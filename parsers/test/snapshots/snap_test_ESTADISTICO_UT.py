# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestESTADISTICO_UT::test_fetch_production 1"] = [
    {
        "datetime": "2025-01-01T00:00:00-06:00",
        "zoneKey": "SV",
        "production": {
            "biomass": 145.81,
            "geothermal": 162.33,
            "hydro": 160.81,
            "unknown": 58.28,
            "wind": 18.08,
        },
        "storage": {},
        "source": "ut.com.sv",
        "sourceType": "measured",
    },
    {
        "datetime": "2025-01-01T01:00:00-06:00",
        "zoneKey": "SV",
        "production": {
            "biomass": 147.53,
            "geothermal": 165.11,
            "hydro": 129.55,
            "unknown": 59.52,
            "wind": 15.79,
        },
        "storage": {},
        "source": "ut.com.sv",
        "sourceType": "measured",
    },
    {
        "datetime": "2025-01-01T02:00:00-06:00",
        "zoneKey": "SV",
        "production": {
            "biomass": 148.04,
            "geothermal": 166.12,
            "hydro": 97.36,
            "unknown": 56.4,
            "wind": 19.01,
        },
        "storage": {},
        "source": "ut.com.sv",
        "sourceType": "measured",
    },
]
