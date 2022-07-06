#!/usr/bin/env python3
# coding=utf-8

"""Parser for Moldova."""

from collections import namedtuple

import arrow
import requests

# Supports the following formats:
# - type=csv for zip-data with semicolon-separated-values
# - type=array for a 2D json-array containing an array for each datapoint
# - type=html for a HTML-table (default when no type is given)
archive_base_url = "https://moldelectrica.md/utils/archive2.php?id=table&type=array"

# Format for date and time used in archive-datapoints.
archive_datetime_format = "YYYY-MM-DD HH:mm"
# Format for date only used in the archive-url.
archive_date_format = "DD.MM.YYYY"

# Fields that can be fetched from archive_url in order.
archive_fields = (
    "datetime",
    "consumption",
    "planned_consumption",
    "production",
    "planned_production",
    "tpp",  # production from thermal power plants
    "hpp",  # production from thermal power plants
    "res",  # production from renewable energy sources
    "exchange_UA_to_MD",
    "planned_exchange_UA_to_MD",
    "exchange_RO_to_MD",
    "planned_exchange_RO_to_MD",
)

# Datapoint in the archive-data.
ArchiveDatapoint = namedtuple("ArchiveDatapoint", archive_fields)

display_url = "http://www.moldelectrica.md/ro/activity/system_state"
data_url = "http://www.moldelectrica.md/utils/load5.php"

# To match the fields with the respective index and meaning,
# I used the following code which may be used in the future for maintenance:
# https://gist.github.com/Impelon/09407f739cdff05134f8c77cb7a92ada

# Fields that can be fetched from data_url linked to production.
# Types of production and translations have been added manually.
production_fields = (
    {"index": 2, "name": "NHE Costeşti", "type": "hydro"},  # run-of-river
    {"index": 3, "name": "CET Nord", "type": "gas"},  # CHPP
    {"index": 4, "name": "NHE Dubăsari", "type": "hydro"},
    {"index": 5, "name": "CET-2 Chişinău", "type": "gas"},  # CHPP
    {"index": 6, "name": "CET-1 Chişinău", "type": "gas"},  # CHPP
    {
        "index": 7,
        "name": "CERS Moldovenească",
        "type": "gas",
    },  # fuel mix: 99.94% gas, 0.01% coal, 0.05% oil (2020)
)
# Other relevant fields that can be fetched from data_url.
other_fields = (
    {"index": 26, "name": "consumption"},
    {"index": 27, "name": "generation"},
    {"index": 28, "name": "exchange UA->MD"},
    {"index": 29, "name": "exchange RO->MD"},
    {"index": 30, "name": "utility frequency"},
)

# Further information on the equipment used at CERS Moldovenească can be found at:
# http://moldgres.com/o-predpriyatii/equipment
# Further information on the fuel-mix used at CERS Moldovenească can be found at:
# http://moldgres.com/search/%D0%9F%D1%80%D0%BE%D0%B8%D0%B7%D0%B2%D0%BE%D0%B4%D1%81%D1%82%D0%B2%D0%B5%D0%BD%D0%BD%D1%8B%D0%B5%20%D0%BF%D0%BE%D0%BA%D0%B0%D0%B7%D0%B0%D1%82%D0%B5%D0%BB%D0%B8
# (by searching for 'Производственные показатели' aka. 'Performance Indicators')
# Data for the fuel-mix at CERS Moldovenească for the year 2020 can be found at:
# http://moldgres.com/wp-content/uploads/2021/02/proizvodstvennye-pokazateli-zao-moldavskaja-gres-za-2020-god.pdf

# Annual reports from moldelectrica can be found at:
# https://moldelectrica.md/ro/network/annual_report


def template_price_response(zone_key, datetime, price) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "currency": "MDL",
        "price": price,
        "source": "moldelectrica.md",
    }


def template_consumption_response(zone_key, datetime, consumption) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "consumption": consumption,
        "source": "moldelectrica.md",
    }


def template_production_response(zone_key, datetime, production) -> dict:
    return {
        "zoneKey": zone_key,
        "datetime": datetime,
        "production": production,
        "storage": {},
        "source": "moldelectrica.md",
    }


def template_exchange_response(sorted_zone_keys, datetime, netflow) -> dict:
    return {
        "sortedZoneKeys": sorted_zone_keys,
        "datetime": datetime,
        "netFlow": netflow,
        "source": "moldelectrica.md",
    }


def get_archive_data(session=None, dates=None) -> list:
    """
    Returns archive data as a list of ArchiveDatapoint.

    Optionally accepts a date to fetch the data for,
    or two dates specifing the range to fetch the data for.
    Specifying a date-range too high will cause errors with the archive-server.
    If no dates are specified data for the last 24 hours is fetched.
    """
    s = session or requests.Session()

    try:
        date1, date2 = sorted(dates)
    except:
        date1 = date2 = dates

    archive_url = archive_base_url
    if date1 and date2:
        archive_url += "&date1={}".format(
            arrow.get(date1).to("Europe/Chisinau").format(archive_date_format)
        )
        archive_url += "&date2={}".format(
            arrow.get(date2).to("Europe/Chisinau").format(archive_date_format)
        )

    data_response = s.get(archive_url, verify=False)
    data = data_response.json()
    try:
        return [
            ArchiveDatapoint(
                arrow.get(
                    entry[0], archive_datetime_format, tzinfo="Europe/Chisinau"
                ).datetime,
                *map(float, entry[1:])
            )
            for entry in data
        ]
    except:
        raise Exception(
            "Not able to parse received data. Check that the specifed URL returns correct data."
        )


def get_data(session=None) -> list:
    """Returns data as a list of floats."""
    s = session or requests.Session()

    # In order for data_url to return data, cookies from display_url must be obtained then reused.
    response = s.get(display_url, verify=False)
    data_response = s.get(data_url, verify=False)
    raw_data = data_response.text
    try:
        data = [float(i) if i else None for i in raw_data.split(",")]
    except:
        raise Exception(
            "Not able to parse received data. Check that the specifed URL returns correct data."
        )

    return data


def fetch_price(zone_key="MD", session=None, target_datetime=None, logger=None) -> dict:
    """
    Returns the static price of electricity (0.145 MDL per kWh) as specified here:
    https://moldelectrica.md/ro/activity/tariff
    It is defined by the following government-agency decision,
    which is still in effect at the time of writing this (July 2021):
    http://lex.justice.md/viewdoc.php?action=view&view=doc&id=360109&lang=1
    """
    if target_datetime:
        raise NotImplementedError(
            "This parser is not yet able to parse past dates for price"
        )

    dt = arrow.now("Europe/Chisinau").datetime
    return template_price_response(zone_key, dt, 145.0)


def fetch_consumption(
    zone_key="MD", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the consumption (in MW) of a given country."""
    if target_datetime:
        archive_data = get_archive_data(session, target_datetime)

        datapoints = []
        for entry in archive_data:
            datapoint = template_consumption_response(
                zone_key, entry.datetime, entry.consumption
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        consumption = field_values[other_fields[0]["index"]]

        dt = arrow.now("Europe/Chisinau").datetime

        datapoint = template_consumption_response(zone_key, dt, consumption)

        return datapoint


def fetch_production(
    zone_key="MD", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the production mix (in MW) of a given country."""
    if target_datetime:
        archive_data = get_archive_data(session, target_datetime)

        datapoints = []
        for entry in archive_data:
            production = {
                "solar": None,
                "wind": None,
                "biomass": 0.0,
                "nuclear": 0.0,
                "gas": 0.0,
                "hydro": 0.0,
            }

            production["gas"] += entry.tpp
            production["hydro"] += entry.hpp
            # Renewables (solar + biogas + wind) make up a small part of the energy produced.
            # The exact mix of renewable enegry sources is unknown,
            # so everything is attributed to biomass.
            production["biomass"] += entry.res

            datapoint = template_production_response(
                zone_key, entry.datetime, production
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        production = {
            "solar": None,
            "wind": None,
            "biomass": 0.0,
            "nuclear": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
        }

        non_renewables_production = 0.0
        for field in production_fields:
            produced = field_values[field["index"]]
            non_renewables_production += produced
            production[field["type"]] += produced

        # Renewables (solar + biogas + wind) make up a small part of the energy produced.
        # They do not have an explicit entry,
        # hence the difference between the actual generation and
        # the sum of all other sectors are the renewables.
        # The exact mix of renewable enegry sources is unknown,
        # so everything is attributed to biomass.
        production["biomass"] = (
            field_values[other_fields[1]["index"]] - non_renewables_production
        )

        dt = arrow.now("Europe/Chisinau").datetime

        datapoint = template_production_response(zone_key, dt, production)

        return datapoint


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    if target_datetime:
        archive_data = get_archive_data(session, target_datetime)

        datapoints = []
        for entry in archive_data:
            if sorted_zone_keys == "MD->UA":
                netflow = -1 * entry.exchange_UA_to_MD
            elif sorted_zone_keys == "MD->RO":
                netflow = -1 * entry.exchange_RO_to_MD
            else:
                raise NotImplementedError("This exchange pair is not implemented")

            datapoint = template_exchange_response(
                sorted_zone_keys, entry.datetime, netflow
            )
            datapoints.append(datapoint)
        return datapoints
    else:
        field_values = get_data(session)

        if sorted_zone_keys == "MD->UA":
            netflow = -1 * field_values[other_fields[2]["index"]]
        elif sorted_zone_keys == "MD->RO":
            netflow = -1 * field_values[other_fields[3]["index"]]
        else:
            raise NotImplementedError("This exchange pair is not implemented")

        dt = arrow.now("Europe/Chisinau").datetime

        datapoint = template_exchange_response(sorted_zone_keys, dt, netflow)

        return datapoint


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    def try_print(callable, *args, **kwargs):
        try:
            result = callable(*args, **kwargs)
            try:
                print("[{}, ... ({} more elements)]".format(result[0], len(result)))
            except:
                print(result)
        except Exception as e:
            print(repr(e))

    for target_datetime in (None, "2021-07-25T15:00"):
        print("For target_datetime {}:".format(target_datetime))
        print("fetch_price() ->")
        try_print(fetch_price, target_datetime=target_datetime)
        print("fetch_consumption() ->")
        try_print(fetch_consumption, target_datetime=target_datetime)
        print("fetch_production() ->")
        try_print(fetch_production, target_datetime=target_datetime)
        print("fetch_exchange(MD, UA) ->")
        try_print(fetch_exchange, "MD", "UA", target_datetime=target_datetime)
        print("fetch_exchange(MD, RO) ->")
        try_print(fetch_exchange, "MD", "RO", target_datetime=target_datetime)
        print("------------")
