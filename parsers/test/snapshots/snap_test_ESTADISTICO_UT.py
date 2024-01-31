# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestESTADISTICO_UT::test_fetch_production 1"] = [
    {
        "datetime": "2023-12-29T00:00:00-06:00",
        "production": {
            "biomass": 152.46,
            "geothermal": 169.52,
            "hydro": 102.3,
            "unknown": 313.71,
            "wind": 11.09,
        },
        "source": "ut.com.sv",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "SV",
    },
    {
        "datetime": "2023-12-29T01:00:00-06:00",
        "production": {
            "biomass": 153.04,
            "geothermal": 169.39,
            "hydro": 109.89,
            "unknown": 282.69,
            "wind": 5.9,
        },
        "source": "ut.com.sv",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "SV",
    },
    {
        "datetime": "2023-12-29T02:00:00-06:00",
        "production": {
            "biomass": 151.57,
            "geothermal": 169.64,
            "hydro": 113.99,
            "unknown": 255.78,
            "wind": 10.01,
        },
        "source": "ut.com.sv",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "SV",
    },
]
