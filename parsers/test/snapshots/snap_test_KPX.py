# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestKPX::test_fetch_consumption 1"] = [
    {
        "consumption": 78866.0,
        "datetime": "2023-09-13T17:40:00+09:00",
        "source": "new.kpx.or.kr",
        "sourceType": "measured",
        "zoneKey": "KR",
    }
]
