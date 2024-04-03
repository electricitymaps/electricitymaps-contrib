# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestENTE::test_fetch_production 1"] = {
    "datetime": "2024-04-03T08:00:00-06:00",
    "production": {"unknown": 1460.3},
    "source": "enteoperador.org",
    "zoneKey": "HN",
}
