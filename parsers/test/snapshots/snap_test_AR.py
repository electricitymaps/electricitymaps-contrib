# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestCammesaweb::test_exchanges_AR_BAS_AR_COM 1"] = []

snapshots["TestCammesaweb::test_exchanges_AR_CL_SEN 1"] = [
    {
        "datetime": "2023-08-30T02:45:00-03:00",
        "netFlow": 200.0,
        "sortedZoneKeys": "AR->CL-SEN",
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
    }
]

snapshots["TestCammesaweb::test_fetch_production 1"] = [
    {
        "datetime": "2023-09-07T00:20:00-03:00",
        "production": {
            "biomass": 161.85,
            "hydro": 6086.5,
            "nuclear": 1388.4,
            "solar": 0.0,
            "unknown": 7487.1,
            "wind": 2009.54,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
    {
        "datetime": "2023-09-07T00:45:00-03:00",
        "production": {
            "biomass": 157.2,
            "hydro": 5893.23,
            "nuclear": 1390.4,
            "solar": 0.0,
            "unknown": 7223.0,
            "wind": 1944.1,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
    {
        "datetime": "2023-09-07T00:50:00-03:00",
        "production": {
            "biomass": 158.55,
            "hydro": 6028.12,
            "nuclear": 1394.0,
            "solar": 0.0,
            "unknown": 7206.0,
            "wind": 1922.51,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
    {
        "datetime": "2023-09-07T01:45:00-03:00",
        "production": {
            "biomass": 148.3,
            "hydro": 6592.0,
            "nuclear": 1394.6,
            "solar": 0.0,
            "unknown": 6802.2,
            "wind": 1900.64,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
    {
        "datetime": "2023-09-07T01:50:00-03:00",
        "production": {
            "biomass": 149.74,
            "hydro": 6678.26,
            "nuclear": 1387.0,
            "solar": 0.0,
            "unknown": 6758.0,
            "wind": 1871.5,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
    {
        "datetime": "2023-09-07T01:55:00-03:00",
        "production": {
            "biomass": 155.96,
            "hydro": 6525.16,
            "nuclear": 1388.1,
            "solar": 0.0,
            "unknown": 6791.2,
            "wind": 1835.68,
        },
        "source": "cammesaweb.cammesa.com",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "AR",
    },
]
