# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestPF::test_fetch_production_live 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-01-01T02:00:00-10:00",
        "production": {"hydro": 0.969, "oil": 54.52, "solar": 6.909},
        "source": "edt.pf",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "PF",
    }
]
