#!/usr/bin/env python3


"""Real time parser for the New England ISO (NEISO) area."""
import logging
import time
from collections import defaultdict
from datetime import timedelta

import arrow
import requests

from parsers.lib.config import refetch_frequency

url = "https://www.iso-ne.com/ws/wsclient"

generation_mapping = {
    "Coal": "coal",
    "NaturalGas": "gas",
    "Wind": "wind",
    "Hydro": "hydro",
    "Nuclear": "nuclear",
    "Wood": "biomass",
    "Oil": "oil",
    "Refuse": "biomass",
    "LandfillGas": "biomass",
    "Solar": "solar",
}


def timestring_converter(time_string):
    """Converts ISO-8601 time strings in neiso data into aware datetime objects."""

    dt_naive = arrow.get(time_string)
    dt_aware = dt_naive.replace(tzinfo="America/New_York").datetime

    return dt_aware


def get_json_data(target_datetime, params, session=None):
    """Fetches json data for requested params and target_datetime using a post request."""

    epoch_time = str(int(time.time()))

    # when target_datetime is None, arrow.get(None) will return current time
    target_datetime = arrow.get(target_datetime)
    target_ne = target_datetime.to("America/New_York")
    target_ne_day = target_ne.format("MM/DD/YYYY")

    postdata = {
        "_nstmp_formDate": epoch_time,
        "_nstmp_startDate": target_ne_day,
        "_nstmp_endDate": target_ne_day,
        "_nstmp_twodays": "false",
        "_nstmp_showtwodays": "false",
    }
    postdata.update(params)

    s = session or requests.Session()

    req = s.post(url, data=postdata)
    json_data = req.json()
    raw_data = json_data[0]["data"]

    return raw_data


def production_data_processer(raw_data, logger) -> list:
    """
    Takes raw json data and removes unnecessary keys.
    Separates datetime key and converts to a datetime object.
    """

    other_keys = {"BeginDateMs", "Renewables", "BeginDate", "Other"}
    known_keys = generation_mapping.keys() | other_keys

    unmapped = set()
    clean_data = []
    counter = 0
    for datapoint in raw_data:
        current_keys = datapoint.keys() | set()
        unknown_keys = current_keys - known_keys
        unmapped = unmapped | unknown_keys

        keys_to_remove = {"BeginDateMs", "Renewables"} | unknown_keys
        for k in keys_to_remove:
            datapoint.pop(k, None)

        time_string = datapoint.pop("BeginDate", None)
        if time_string:
            dt = timestring_converter(time_string)
        else:
            # passing None to arrow.get() will return current time
            counter += 1
            logger.warning(
                "Skipping US-NEISO datapoint missing timestamp.",
                extra={"key": "US-NEISO"},
            )
            continue

        # neiso storage flow signs are opposite to EM
        battery_storage = -1 * datapoint.pop("Other", 0.0)

        production = defaultdict(lambda: 0.0)
        for k, v in datapoint.items():
            # Need to avoid duplicate keys overwriting.
            production[generation_mapping[k]] += v

        # move small negative values to 0
        for k, v in production.items():
            if -5 < v < 0:
                production[k] = 0

        clean_data.append((dt, dict(production), battery_storage))

    for key in unmapped:
        logger.warning(
            "Key '{}' in US-NEISO is not mapped to type.".format(key),
            extra={"key": "US-NEISO"},
        )

    if counter > 0:
        logger.warning(
            "Skipped {} US-NEISO datapoints that were missing timestamps.".format(
                counter
            ),
            extra={"key": "US-NEISO"},
        )

    return sorted(clean_data)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key="US-NEISO",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> list:
    """Requests the last known production mix (in MW) of a given country."""

    postdata = {
        "_nstmp_chartTitle": "Fuel+Mix+Graph",
        "_nstmp_requestType": "genfuelmix",
        "_nstmp_fuelType": "all",
        "_nstmp_height": "250",
    }

    production_json = get_json_data(target_datetime, postdata, session)
    points = production_data_processer(production_json, logger)

    # Hydro pumped storage is included within the general hydro category.
    production_mix = []
    for item in points:
        data = {
            "zoneKey": zone_key,
            "datetime": item[0],
            "production": item[1],
            "storage": {"hydro": None, "battery": item[2]},
            "source": "iso-ne.com",
        }
        production_mix.append(data)

    return production_mix


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    # For directions, note that ISO-NE always reports its import as negative

    if sorted_zone_keys == "CA-NB->US-NEISO" or sorted_zone_keys == "CA-NB->US-NE-ISNE":
        # CA-NB->US-NEISO means import to NEISO should be positive
        multiplier = -1

        postdata = {"_nstmp_zone0": "4010"}  # ".I.SALBRYNB345 1"

    elif (
        sorted_zone_keys == "CA-QC->US-NEISO" or sorted_zone_keys == "CA-QC->US-NE-ISNE"
    ):
        # CA-QC->US-NEISO means import to NEISO should be positive
        multiplier = -1

        postdata = {
            "_nstmp_zone0": "4012",  # ".I.HQ_P1_P2345 5"
            "_nstmp_zone1": "4013",  # ".I.HQHIGATE120 2"
        }

    elif (
        sorted_zone_keys == "US-NEISO->US-NY"
        or sorted_zone_keys == "US-NE-ISNE->US-NY-NYIS"
    ):
        # US-NEISO->US-NY means import to NEISO should be negative
        multiplier = 1

        postdata = {
            "_nstmp_zone0": "4014",  # ".I.SHOREHAM138 99"
            "_nstmp_zone1": "4017",  # ".I.NRTHPORT138 5"
            "_nstmp_zone2": "4011",  # ".I.ROSETON 345 1"
        }

    else:
        raise Exception("Exchange pair not supported: {}".format(sorted_zone_keys))

    postdata["_nstmp_requestType"] = "externalflow"

    exchange_data = get_json_data(target_datetime, postdata, session)

    summed_exchanges = defaultdict(int)
    for exchange_key, exchange_values in exchange_data.items():
        # sum up values from separate "exchanges" for the same date.
        # this works because the timestamp of exchanges is always reported
        # in exact 5-minute intervals by the API,
        # e.g. "2018-03-18T00:05:00.000-04:00"
        for datapoint in exchange_values:
            dt = timestring_converter(datapoint["BeginDate"])
            summed_exchanges[dt] += datapoint["Actual"]

    result = [
        {
            "datetime": timestamp,
            "sortedZoneKeys": sorted_zone_keys,
            "netFlow": value * multiplier,
            "source": "iso-ne.com",
        }
        for timestamp, value in summed_exchanges.items()
    ]

    return result


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print("fetch_production() ->")
    pprint(fetch_production())

    print('fetch_production(target_datetime=arrow.get("2017-12-31T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2017-12-31T12:00Z")))

    print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z")))

    print('fetch_exchange("US-NEISO", "CA-QC") ->')
    pprint(fetch_exchange("US-NEISO", "CA-QC"))

    print(
        'fetch_exchange("US-NEISO", "CA-QC", target_datetime=arrow.get("2017-12-31T12:00Z")) ->'
    )
    pprint(
        fetch_exchange(
            "US-NEISO", "CA-QC", target_datetime=arrow.get("2017-12-31T12:00Z")
        )
    )

    print(
        'fetch_exchange("US-NEISO", "CA-QC", target_datetime=arrow.get("2007-03-13T12:00Z")) ->'
    )
    pprint(
        fetch_exchange(
            "US-NEISO", "CA-QC", target_datetime=arrow.get("2007-03-13T12:00Z")
        )
    )
