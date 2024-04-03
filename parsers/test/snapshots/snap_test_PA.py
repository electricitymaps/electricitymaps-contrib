# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestPA::test_fetch_consumption 1"] = [
    {
        "consumption": 1314.0,
        "datetime": "2024-04-02T15:30:29-05:00",
        "source": "sitr.cnd.com.pa",
        "sourceType": "measured",
        "zoneKey": "PA",
    }
]

snapshots["TestPA::test_fetch_exchange_live 1"] = [
    {
        "datetime": "2024-04-02T15:31:45-05:00",
        "netFlow": -78.4,
        "sortedZoneKeys": "CR->PA",
        "source": "sitr.cnd.com.pa",
        "sourceType": "measured",
    }
]

snapshots["TestPA::test_fetch_production_live 1"] = [
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
            "wind": 115.4,
        },
        "source": "sitr.cnd.com.pa",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "PA",
    }
]

snapshots["TestPA::test_fetch_production_live 2"] = [
    {
        "correctedModes": [],
        "datetime": "2024-04-03T02:43:25-05:00",
        "production": {
            "biomass": 21.49,
            "coal": 0.0,
            "gas": 358.12,
            "hydro": 554.19,
            "oil": 278.72,
            "solar": 0.0,
            "wind": 17.8,
        },
        "source": "sitr.cnd.com.pa",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "PA",
    }
]
