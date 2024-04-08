# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import GenericRepr, Snapshot

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
        "datetime": "2019-12-31T20:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("592"),
            "solar": GenericRepr("21"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2019-12-31T21:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("486"),
            "solar": GenericRepr("19"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2019-12-31T22:00:00+00:00",
        "production": {
            "gas": GenericRepr("618"),
            "hydro": GenericRepr("435"),
            "solar": GenericRepr("16"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2019-12-31T23:00:00+00:00",
        "production": {
            "gas": GenericRepr("618"),
            "hydro": GenericRepr("408"),
            "solar": GenericRepr("16"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T00:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("348"),
            "solar": GenericRepr("19"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T01:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("323"),
            "solar": GenericRepr("15"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T02:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("321"),
            "solar": GenericRepr("7"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T03:00:00+00:00",
        "production": {
            "gas": GenericRepr("619"),
            "hydro": GenericRepr("333"),
            "solar": GenericRepr("7"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T04:00:00+00:00",
        "production": {
            "gas": GenericRepr("618"),
            "hydro": GenericRepr("339"),
            "solar": GenericRepr("7"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T05:00:00+00:00",
        "production": {
            "gas": GenericRepr("618"),
            "hydro": GenericRepr("381"),
            "solar": GenericRepr("5"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T06:00:00+00:00",
        "production": {
            "gas": GenericRepr("615"),
            "hydro": GenericRepr("482"),
            "solar": GenericRepr("2"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T07:00:00+00:00",
        "production": {
            "gas": GenericRepr("611"),
            "hydro": GenericRepr("551"),
            "solar": GenericRepr("3"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T08:00:00+00:00",
        "production": {
            "gas": GenericRepr("608"),
            "hydro": GenericRepr("567"),
            "solar": GenericRepr("8"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T09:00:00+00:00",
        "production": {
            "gas": GenericRepr("604"),
            "hydro": GenericRepr("577"),
            "solar": GenericRepr("9"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T10:00:00+00:00",
        "production": {
            "gas": GenericRepr("604"),
            "hydro": GenericRepr("569"),
            "solar": GenericRepr("14"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T11:00:00+00:00",
        "production": {
            "gas": GenericRepr("605"),
            "hydro": GenericRepr("561"),
            "solar": GenericRepr("17"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T12:00:00+00:00",
        "production": {
            "gas": GenericRepr("604"),
            "hydro": GenericRepr("562"),
            "solar": GenericRepr("18"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T13:00:00+00:00",
        "production": {
            "gas": GenericRepr("606"),
            "hydro": GenericRepr("597"),
            "solar": GenericRepr("21"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T14:00:00+00:00",
        "production": {
            "gas": GenericRepr("607"),
            "hydro": GenericRepr("700"),
            "solar": GenericRepr("21"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T15:00:00+00:00",
        "production": {
            "gas": GenericRepr("607"),
            "hydro": GenericRepr("718"),
            "solar": GenericRepr("21"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T16:00:00+00:00",
        "production": {
            "gas": GenericRepr("606"),
            "hydro": GenericRepr("701"),
            "solar": GenericRepr("21"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T17:00:00+00:00",
        "production": {
            "gas": GenericRepr("610"),
            "hydro": GenericRepr("681"),
            "solar": GenericRepr("20"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T18:00:00+00:00",
        "production": {
            "gas": GenericRepr("608"),
            "hydro": GenericRepr("662"),
            "solar": GenericRepr("18"),
            "wind": GenericRepr("0"),
        },
        "source": "gse.com.ge",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "GE",
    },
    {
        "correctedModes": [],
        "datetime": "2020-01-01T19:00:00+00:00",
        "production": {
            "gas": GenericRepr("608"),
            "hydro": GenericRepr("585"),
            "solar": GenericRepr("20"),
            "wind": GenericRepr("0"),
        },
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
