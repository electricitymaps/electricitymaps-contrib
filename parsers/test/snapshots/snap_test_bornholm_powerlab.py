# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestBornholmPowerlab::test_fetch_exchange 1"] = [
    {
        "datetime": "2023-09-13T12:29:40+00:00",
        "netFlow": -15.4,
        "sortedZoneKeys": "DK-BHM->SE-SE4",
        "source": "bornholm.powerlab.dk",
        "sourceType": "measured",
    }
]

snapshots["TestBornholmPowerlab::test_fetch_production 1"] = [
    {
        "datetime": "2023-09-13T12:29:40+00:00",
        "production": {"biomass": 1.2, "solar": 3.6, "wind": 8.2},
        "source": "bornholm.powerlab.dk",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "DK-BHM",
    }
]
