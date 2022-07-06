#!/usr/bin/python

"""
Test datapoints for quality.py
Each one is designed to test some part of the validation functions.
"""

import datetime

dt = datetime.datetime.utcnow()

prod = {
    "biomass": 15.0,
    "coal": 130.0,
    "gas": 890.0,
    "hydro": 500.0,
    "nuclear": 345.7,
    "oil": 0.0,
    "solar": 60.0,
    "wind": 75.0,
    "geothermal": None,
    "unknown": 3.0,
}

c1 = {
    "consumption": 1374.0,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

c2 = {
    "consumption": -1081.0,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

c3 = {
    "consumption": None,
    "zoneKey": "FR",
    "datetime": dt,
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

e1 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": dt,
    "netFlow": 73.0,
    "source": "mysource.com",
}

e2 = {"sortedZoneKeys": "DK->NO", "netFlow": 73.0, "source": "mysource.com"}

e3 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": "At the 3rd beep the time will be......",
    "netFlow": 73.0,
    "source": "mysource.com",
}

future = datetime.datetime.utcnow() + datetime.timedelta(seconds=5 * 60)

e4 = {
    "sortedZoneKeys": "DK->NO",
    "datetime": future,
    "netFlow": 73.0,
    "source": "mysource.com",
}

p1 = {
    "zoneKey": "FR",
    "production": prod,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p2 = {
    "production": prod,
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p3 = {
    "zoneKey": "FR",
    "production": prod,
    "datetime": "13th May 2017",
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p4 = {
    "zoneKey": "BR",
    "production": prod,
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p5 = {
    "zoneKey": "BR",
    "production": prod,
    "datetime": future,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p6 = {
    "zoneKey": "FR",
    "production": {
        "biomass": 10.0,
        "coal": None,
        "gas": None,
        "hydro": 340.2,
        "nuclear": 2390.0,
        "oil": None,
        "solar": 49.0,
        "wind": 0.0,
        "geothermal": 453.8,
        "unknown": None,
    },
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p7 = {
    "zoneKey": "CH",
    "production": {
        "biomass": 10.0,
        "coal": None,
        "gas": 780.0,
        "hydro": 340.2,
        "nuclear": 2390.0,
        "oil": None,
        "solar": 49.0,
        "wind": 0.0,
        "geothermal": 453.8,
        "unknown": None,
    },
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p8 = {
    "zoneKey": "FR",
    "production": {
        "biomass": 10.0,
        "coal": 230.6,
        "gas": 780.0,
        "hydro": 340.2,
        "nuclear": 2390.0,
        "oil": 0.0,
        "solar": 49.0,
        "wind": 0.0,
        "geothermal": -453.8,
        "unknown": 0.0,
    },
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p9 = {
    "zoneKey": "FR",
    "production": {
        "biomass": 10.0,
        "coal": 230.6,
        "gas": 780.0,
        "hydro": 340.2,
        "nuclear": 2390.0,
        "oil": 0.0,
        "solar": 49.0,
        "wind": 0.0,
        "geothermal": 453.8,
        "unknown": 10.0,
    },
    "datetime": dt,
    "storage": {
        "hydro": -10.0,
    },
    "source": "mysource.com",
}

p10 = {
    "zoneKey": "DE",
    "production": {
        "coal": 230.6,
        "gas": 780.0,
        "hydro": 340.2,
        "nuclear": 2390.0,
        "oil": 0.0,
        "solar": 49.0,
        "wind": 0.0,
        "geothermal": 453.8,
        "unknown": 10.0,
    },
    "datetime": dt,
    "source": "mysource.com",
}

p11 = {
    "zoneKey": "PL",
    "production": {"coal": 230.6, "gas": 780.0},
    "datetime": dt,
    "source": "mysource.com",
}

p12 = {
    "zoneKey": "SI",
    "production": {
        "biomass": 15,
        "coal": 4000,
        "gas": 14,
        "geothermal": None,
        "hydro": 856,
        "nuclear": 692,
        "oil": 0,
        "solar": 94,
        "unknown": None,
        "wind": 1,
    },
    "datetime": dt,
    "source": "mysource.com",
}

p13 = {
    "zoneKey": "DK-DK1",
    "production": {
        "oil": 1,
        "unknown": 79,
        "coal": 534,
        "wind": 2000,
        "biomass": 583,
        "gas": 215,
    },
    "datetime": dt,
    "source": "entsoe.eu",
}

p14 = {
    "zoneKey": "FI",
    "production": {
        "nuclear": 2565,
        "oil": 1,
        "unknown": 79,
        "coal": 534,
        "hydro": 2176,
        "wind": 42,
        "biomass": 583,
        "gas": 215,
        "geothermal": None,
        "solar": None,
    },
    "datetime": dt,
    "source": "entsoe.eu",
}
