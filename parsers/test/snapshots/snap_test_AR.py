# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots[
    "TestCammesaweb::test_exchanges_AR_BAS_AR_COM 1"
] = []  # Empty for now as subregions for AR are not yet implemented.

snapshots["TestCammesaweb::test_exchanges_AR_CL_SEN 1"] = [
    {
        "datetime": "2023-08-30T02:45:00-03:00",
        "netFlow": 200.0,
        "sortedZoneKeys": "AR->CL-SEN",
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
    }
]
