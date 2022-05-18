#!/usr/bin/env python3
# The arrow library is used to handle datetimes
import logging
from datetime import timedelta

import arrow

# The request library is used to fetch content through HTTP
import requests

from parsers.lib.config import refetch_frequency

exchanges_mapping = {
    "BY->LT": ["BY->LT"],
    "DE->DK-DK1": [
        "DE->DK1",
    ],
    "DE->DK-DK2": [
        "DE->DK2",
    ],
    "DE->SE": ["DE->SE4"],
    "DE->SE-SE4": ["DE->SE4"],
    "DK-DK1->NO": ["DK1->NO2"],
    "DK-DK1->NO-NO2": ["DK1->NO2"],
    "DK-DK1->SE": ["DK1->SE3"],
    "DK-DK1->SE-SE3": ["DK1->SE3"],
    "DK-DK2->SE": ["DK2->SE4"],
    "DK-DK2->SE-SE4": ["DK2->SE4"],
    "EE->RU": ["EE->RU"],
    "EE->RU-1": ["EE->RU"],
    "EE->LV": ["EE->LV"],
    "EE->FI": ["EE->FI"],
    "FI->NO": ["FI->NO4"],
    "FI->NO-NO4": ["FI->NO4"],
    "FI->RU": ["FI->RU"],
    "FI->RU-1": ["FI->RU"],
    "FI->SE": ["FI->SE1", "FI->SE3"],
    "FI->SE-SE1": [
        "FI->SE1",
    ],
    "FI->SE-SE3": ["FI->SE3"],
    "LT->LV": ["LT->LV"],
    "LT->SE": ["LT->SE4"],
    "LT->SE-SE4": ["LT->SE4"],
    "LT->PL": ["LT->PL"],
    "LT->RU-KGD": ["LT->RU"],
    "LV->RU": ["LV->RU"],
    "LV->RU-1": ["LV->RU"],
    "NL->NO": ["NL->NO2"],
    "NL->NO-NO2": ["NL->NO2"],
    "NO->SE": ["NO1->SE3", "NO3->SE2", "NO4->SE1", "NO4->SE2"],
    "NO-NO1->NO-NO2": ["NO1->NO2"],
    "NO-NO1->NO-NO3": ["NO1->NO3"],
    "NO-NO1->NO-NO5": ["NO1->NO5"],
    "NO-NO1->SE": ["NO1->SE3"],
    "NO-NO2->NO-NO5": ["NO2->NO5"],
    "NO-NO3->NO-NO4": ["NO3->NO4"],
    "NO-NO3->NO-NO5": ["NO3->NO5"],
    "NO-NO3->SE": ["NO3->SE2"],
    "NO-NO3->SE-SE2": ["NO3->SE2"],
    "NO->RU": ["NO4->RU"],
    "NO->RU-1": ["NO4->RU"],
    "NO-NO4->RU": ["NO4->RU"],
    "NO-NO4->RU-1": ["NO4->RU"],
    "NO-NO4->SE": ["NO4->SE1", "NO4->SE2"],
    "PL->SE": [
        "PL->SE4",
    ],
    "PL->SE-SE4": ["PL->SE4"],
    "SE-SE1->SE-SE2": ["SE1->SE2"],
    "SE-SE2->SE-SE3": ["SE1->SE2"],
    "SE-SE3->SE-SE4": ["SE1->SE2"],
}

# Mappings used to go from country to bidding zone level


@refetch_frequency(timedelta(hours=1))
def fetch_production(
    zone_key="SE",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    r = session or requests.session()
    timestamp = (
        target_datetime.timestamp() if target_datetime else arrow.now().timestamp
    ) * 1000
    url = (
        "http://driftsdata.statnett.no/restapi/ProductionConsumption/GetLatestDetailedOverview?timestamp=%d"
        % timestamp
    )
    response = r.get(url)
    obj = response.json()

    data = {
        "zoneKey": zone_key,
        "production": {
            "nuclear": float(
                list(
                    filter(
                        lambda x: x["titleTranslationId"]
                        == "ProductionConsumption.%s%sDesc" % ("Nuclear", zone_key),
                        obj["NuclearData"],
                    )
                )[0]["value"].replace("\xa0", "")
            ),
            "hydro": float(
                list(
                    filter(
                        lambda x: x["titleTranslationId"]
                        == "ProductionConsumption.%s%sDesc" % ("Hydro", zone_key),
                        obj["HydroData"],
                    )
                )[0]["value"].replace("\xa0", "")
            ),
            "wind": float(
                list(
                    filter(
                        lambda x: x["titleTranslationId"]
                        == "ProductionConsumption.%s%sDesc" % ("Wind", zone_key),
                        obj["WindData"],
                    )
                )[0]["value"].replace("\xa0", "")
            ),
            "unknown": float(
                list(
                    filter(
                        lambda x: x["titleTranslationId"]
                        == "ProductionConsumption.%s%sDesc" % ("Thermal", zone_key),
                        obj["ThermalData"],
                    )
                )[0]["value"].replace("\xa0", "")
            )
            + float(
                list(
                    filter(
                        lambda x: x["titleTranslationId"]
                        == "ProductionConsumption.%s%sDesc"
                        % ("NotSpecified", zone_key),
                        obj["NotSpecifiedData"],
                    )
                )[0]["value"].replace("\xa0", "")
            ),
        },
        "storage": {},
        "source": "driftsdata.stattnet.no",
    }
    data["datetime"] = arrow.get(obj["MeasuredAt"] / 1000).datetime

    return data


@refetch_frequency(timedelta(hours=1))
def fetch_exchange_by_bidding_zone(
    bidding_zone1="DK1",
    bidding_zone2="NO2",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    # Convert bidding zone names into statnett zones
    bidding_zone_1_trimmed, bidding_zone_2_trimmed = [
        x.split("-")[-1] for x in [bidding_zone1, bidding_zone2]
    ]
    bidding_zone_a, bidding_zone_b = sorted(
        [bidding_zone_1_trimmed, bidding_zone_2_trimmed]
    )
    r = session or requests.session()
    timestamp = (
        target_datetime.timestamp() if target_datetime else arrow.now().timestamp
    ) * 1000
    url = (
        "http://driftsdata.statnett.no/restapi/PhysicalFlowMap/GetFlow?Ticks=%d"
        % timestamp
    )
    response = r.get(url)
    obj = response.json()

    exchange = list(
        filter(
            lambda x: set([x["OutAreaElspotId"], x["InAreaElspotId"]])
            == set([bidding_zone_a, bidding_zone_b]),
            obj,
        )
    )[0]

    return {
        "sortedZoneKeys": "->".join(sorted([bidding_zone1, bidding_zone2])),
        "netFlow": exchange["Value"]
        if bidding_zone_a == exchange["OutAreaElspotId"]
        else -1 * exchange["Value"],
        "datetime": arrow.get(obj[0]["MeasureDate"] / 1000).datetime,
        "source": "driftsdata.stattnet.no",
    }


def _fetch_exchanges_from_sorted_bidding_zones(
    sorted_bidding_zones, session=None, target_datetime=None
):
    zones = sorted_bidding_zones.split("->")
    return fetch_exchange_by_bidding_zone(zones[0], zones[1], session, target_datetime)


def _sum_of_exchanges(exchanges):
    exchange_list = list(exchanges)
    return {
        "netFlow": sum(e["netFlow"] for e in exchange_list),
        "datetime": exchange_list[0]["datetime"],
        "source": exchange_list[0]["source"],
    }


@refetch_frequency(timedelta(hours=1))
def fetch_exchange(
    zone_key1="DK",
    zone_key2="NO",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    r = session or requests.session()

    sorted_exchange = "->".join(sorted([zone_key1, zone_key2]))
    data = _sum_of_exchanges(
        map(
            lambda e: _fetch_exchanges_from_sorted_bidding_zones(e, r, target_datetime),
            exchanges_mapping[sorted_exchange],
        )
    )
    data["sortedZoneKeys"] = "->".join(sorted([zone_key1, zone_key2]))

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production(SE) ->")
    print(fetch_production("SE"))
    print("fetch_exchange(NO, SE) ->")
    print(fetch_exchange("NO", "SE"))
    print("fetch_exchange(NO-NO4, RU-1) ->")
    print(fetch_exchange("NO-NO4", "RU-1"))
    print("fetch_exchange(EE, RU-1) ->")
    print(fetch_exchange("EE", "RU-1"))
