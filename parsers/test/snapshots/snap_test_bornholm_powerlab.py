# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestBornholmPowerlab::test_fetch_production 1"] = [
    {
        "datetime": "2023-09-13T14:29:40+02:00",
        "production": {"biomass": 1.2, "solar": 3.6, "wind": 8.2},
        "source": "bornholm.powerlab.dk",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "DK-BHM",
    }
]
