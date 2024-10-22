# snapshottest: v1 - https://goo.gl/zC4yUc

from snapshottest import Snapshot

snapshots = Snapshot()

snapshots["TestFetchProduction::test_production_with_snapshot 1"] = [
    {
        "correctedModes": [],
        "datetime": "2024-01-01T00:00:00+11:00",
        "production": {"coal": 23.7, "hydro": 35.9, "oil": 32, "solar": 0.3, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T01:00:00+11:00",
        "production": {"coal": 20.7, "hydro": 35.2, "oil": 32.3, "solar": 0, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T02:00:00+11:00",
        "production": {"coal": 16.8, "hydro": 35.7, "oil": 33.8, "solar": 0, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T03:00:00+11:00",
        "production": {"coal": 21.1, "hydro": 28.8, "oil": 32, "solar": 0, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T04:00:00+11:00",
        "production": {"coal": 28.4, "hydro": 21, "oil": 32.6, "solar": 0, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T05:00:00+11:00",
        "production": {
            "coal": 27.8,
            "hydro": 23.5,
            "oil": 33.6,
            "solar": 0.1,
            "wind": 0,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T06:00:00+11:00",
        "production": {
            "coal": 16.6,
            "hydro": 34.5,
            "oil": 33.7,
            "solar": 3.6,
            "wind": 0,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T07:00:00+11:00",
        "production": {"coal": 20.2, "hydro": 14, "oil": 32.5, "solar": 20, "wind": 0},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T08:00:00+11:00",
        "production": {
            "coal": 18.3,
            "hydro": 0.3,
            "oil": 27.3,
            "solar": 34.6,
            "wind": 0,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T09:00:00+11:00",
        "production": {
            "coal": 12.8,
            "hydro": 0.8,
            "oil": 9.5,
            "solar": 55.3,
            "wind": 0.2,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T10:00:00+11:00",
        "production": {
            "coal": 11.5,
            "hydro": 1.4,
            "oil": 5.9,
            "solar": 53.1,
            "wind": 1.3,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T11:00:00+11:00",
        "production": {
            "coal": 9.4,
            "hydro": 6.8,
            "oil": 10.9,
            "solar": 48.9,
            "wind": 2,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T12:00:00+11:00",
        "production": {
            "coal": 13.1,
            "hydro": 10.2,
            "oil": 27.9,
            "solar": 41.5,
            "wind": 3.4,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T13:00:00+11:00",
        "production": {
            "coal": 16.5,
            "hydro": 1.4,
            "oil": 23.5,
            "solar": 39.2,
            "wind": 3.2,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T14:00:00+11:00",
        "production": {
            "coal": 21.5,
            "hydro": 6.8,
            "oil": 17.8,
            "solar": 24.6,
            "wind": 2.4,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T15:00:00+11:00",
        "production": {
            "coal": 18.5,
            "hydro": 17.2,
            "oil": 32,
            "solar": 18.7,
            "wind": 2.1,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T16:00:00+11:00",
        "production": {
            "coal": 18.4,
            "hydro": 34.6,
            "oil": 36.4,
            "solar": 14.2,
            "wind": 2.2,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T17:00:00+11:00",
        "production": {
            "coal": 20,
            "hydro": 34.6,
            "oil": 33.9,
            "solar": 10.3,
            "wind": 0.6,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T18:00:00+11:00",
        "production": {
            "coal": 19.8,
            "hydro": 37.5,
            "oil": 34.9,
            "solar": 3.1,
            "wind": 0,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T19:00:00+11:00",
        "production": {
            "coal": 21.3,
            "hydro": 38.7,
            "oil": 42.4,
            "solar": 1.2,
            "wind": 0,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T20:00:00+11:00",
        "production": {"coal": 21.5, "hydro": 39, "oil": 44, "solar": 0.5, "wind": 0.1},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T21:00:00+11:00",
        "production": {
            "coal": 20.2,
            "hydro": 38.7,
            "oil": 42.5,
            "solar": 0,
            "wind": 1.9,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T22:00:00+11:00",
        "production": {"coal": 19, "hydro": 38.6, "oil": 37.1, "solar": 0, "wind": 3.2},
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
    {
        "correctedModes": [],
        "datetime": "2024-01-01T23:00:00+11:00",
        "production": {
            "coal": 17.3,
            "hydro": 38.4,
            "oil": 32,
            "solar": 0.3,
            "wind": 2.8,
        },
        "source": "enercal.nc",
        "sourceType": "measured",
        "storage": {},
        "zoneKey": "NC",
    },
]