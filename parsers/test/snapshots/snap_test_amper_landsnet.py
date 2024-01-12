# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestLandsnet::test_fetch_production 1"] = [
    {
        "datetime": "2023-12-19T15:53:23.729935+00:00",
        "production": {"geothermal": 653.1291, "hydro": 1588.2567, "oil": 0.0},
        "source": "amper.landsnet.is",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "IS",
    }
]
