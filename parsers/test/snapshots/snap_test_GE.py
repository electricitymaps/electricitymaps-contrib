# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["test_fetch_exchange_live[AM] 1"] = [
    {
        "datetime": "2024-04-08T12:00:00+00:00",
        "netFlow": 0.0,
        "sortedZoneKeys": "AM->GE",
        "source": "gse.com.ge",
        "sourceType": "measured",
    }
]

snapshots["test_fetch_exchange_live[AZ] 1"] = [
    {
        "datetime": "2024-04-08T12:00:00+00:00",
        "netFlow": -20.295879,
        "sortedZoneKeys": "AZ->GE",
        "source": "gse.com.ge",
        "sourceType": "measured",
    }
]

snapshots["test_fetch_exchange_live[RU-1] 1"] = [
    {
        "datetime": "2024-04-08T12:00:00+00:00",
        "netFlow": -16.0,
        "sortedZoneKeys": "GE->RU-1",
        "source": "gse.com.ge",
        "sourceType": "measured",
    }
]

snapshots["test_fetch_exchange_live[TR] 1"] = [
    {
        "datetime": "2024-04-08T12:00:00+00:00",
        "netFlow": 0.0,
        "sortedZoneKeys": "GE->TR",
        "source": "gse.com.ge",
        "sourceType": "measured",
    }
]

snapshots["test_fetch_production_historical 1"] = [
    {
        "correctedModes": [],
        "datetime": "2020-01-01T00:00:00+00:00",
        "production": {"gas": 619, "hydro": 348, "solar": 19, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T01:00:00+00:00",
        "production": {"gas": 619, "hydro": 323, "solar": 15, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T02:00:00+00:00",
        "production": {"gas": 619, "hydro": 321, "solar": 7, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T03:00:00+00:00",
        "production": {"gas": 619, "hydro": 333, "solar": 7, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T04:00:00+00:00",
        "production": {"gas": 618, "hydro": 339, "solar": 7, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T05:00:00+00:00",
        "production": {"gas": 618, "hydro": 381, "solar": 5, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T06:00:00+00:00",
        "production": {"gas": 615, "hydro": 482, "solar": 2, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T07:00:00+00:00",
        "production": {"gas": 611, "hydro": 551, "solar": 3, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T08:00:00+00:00",
        "production": {"gas": 608, "hydro": 567, "solar": 8, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T09:00:00+00:00",
        "production": {"gas": 604, "hydro": 577, "solar": 9, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T10:00:00+00:00",
        "production": {"gas": 604, "hydro": 569, "solar": 14, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T11:00:00+00:00",
        "production": {"gas": 605, "hydro": 561, "solar": 17, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T12:00:00+00:00",
        "production": {"gas": 604, "hydro": 562, "solar": 18, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T13:00:00+00:00",
        "production": {"gas": 606, "hydro": 597, "solar": 21, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T14:00:00+00:00",
        "production": {"gas": 607, "hydro": 700, "solar": 21, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T15:00:00+00:00",
        "production": {"gas": 607, "hydro": 718, "solar": 21, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T16:00:00+00:00",
        "production": {"gas": 606, "hydro": 701, "solar": 21, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T17:00:00+00:00",
        "production": {"gas": 610, "hydro": 681, "solar": 20, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T18:00:00+00:00",
        "production": {"gas": 608, "hydro": 662, "solar": 18, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T19:00:00+00:00",
        "production": {"gas": 608, "hydro": 585, "solar": 20, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T20:00:00+00:00",
        "production": {"gas": 611, "hydro": 505, "solar": 21, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T21:00:00+00:00",
        "production": {"gas": 613, "hydro": 406, "solar": 20, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T22:00:00+00:00",
        "production": {"gas": 614, "hydro": 371, "solar": 19, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T23:00:00+00:00",
        "production": {"gas": 616, "hydro": 387, "solar": 19, "wind": 0},
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
]

snapshots["test_fetch_production_live 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-04-08T12:00:00+00:00",
        "production": {
            "gas": 429.450073,
            "hydro": 1293.284424,
            "solar": 0,
            "wind": 17.090729,
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    }
]
