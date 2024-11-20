# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestFetchProduction::test_snapshot_price_data 1"] = [
    {
        "currency": "NZD",
        "datetime": "2024-04-24T18:00:00+00:00",
        "price": 112.44076923076923,
        "source": "api.em6.co.nz",
        "zoneKey": "NZ",
    },
    {
        "currency": "NZD",
        "datetime": "2024-04-24T18:30:00+00:00",
        "price": 79.8623076923077,
        "source": "api.em6.co.nz",
        "zoneKey": "NZ",
    },
]

snapshots["TestFetchProduction::test_snapshot_production_data 1"] = [
    {
        "capacity": {
            "battery storage": 35,
            "coal": 750,
            "gas": 1280,
            "geothermal": 1062,
            "hydro": 5415,
            "nuclear": 0,
            "oil": 156,
            "solar": 47,
            "unknown": 168,
            "wind": 1259,
        },
        "datetime": "2024-04-24T17:30:00+00:00",
        "production": {
            "coal": 156,
            "gas": 188,
            "geothermal": 968,
            "hydro": 1560,
            "nuclear": 0,
            "oil": 0,
            "solar": 0,
            "unknown": 118,
            "wind": 784,
        },
        "source": "transpower.co.nz",
        "storage": {"battery": 0},
        "zoneKey": "NZ",
    },
    {
        "capacity": {
            "battery storage": 35,
            "coal": 750,
            "gas": 1280,
            "geothermal": 1062,
            "hydro": 5415,
            "nuclear": 0,
            "oil": 156,
            "solar": 47,
            "unknown": 168,
            "wind": 1259,
        },
        "datetime": "2024-04-24T18:00:00+00:00",
        "production": {
            "coal": 156,
            "gas": 252,
            "geothermal": 964,
            "hydro": 1644,
            "nuclear": 0,
            "oil": 0,
            "solar": 0,
            "unknown": 117,
            "wind": 814,
        },
        "source": "transpower.co.nz",
        "storage": {"battery": 0},
        "zoneKey": "NZ",
    },
]
