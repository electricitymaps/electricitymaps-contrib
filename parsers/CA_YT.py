#!/usr/bin/env python3

import arrow
import requests
from bs4 import BeautifulSoup

timezone = "America/Whitehorse"


def fetch_production(
    zone_key="CA-YT", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known production mix (in MW) of a given region."""

    """
    We are using Yukon Energy's data from
    http://www.yukonenergy.ca/energy-in-yukon/electricity-101/current-energy-consumption

    Generation in Yukon is done with hydro, diesel oil, and LNG.

    There are two companies, Yukon Energy and ATCO aka Yukon Electric aka YECL.
    Yukon Energy does most of the generation and feeds into Yukon's grid.
    ATCO does operations, billing, and generation in some of the off-grid communities.

    See schema of the grid at http://www.atcoelectricyukon.com/About-Us/

    Per https://en.wikipedia.org/wiki/Yukon#Municipalities_by_population
    of total population 35874 (2016 census), 28238 are in municipalities
    that are connected to the grid - that is 78.7%.

    Off-grid generation is with diesel generators, this is not reported online as of 2017-06-23
    and is not included in this calculation.

    Yukon Energy reports only "hydro" and "thermal" generation.
    Per http://www.yukonenergy.ca/ask-janet/lng-and-boil-off-gas,
    in 2016 the thermal generation was about 50% diesel and 50% LNG.
    But since Yukon Energy doesn't break it down on their website,
    we return all thermal as "unknown".

    Per https://en.wikipedia.org/wiki/List_of_generating_stations_in_Yukon
    Yukon Energy operates about 98% of Yukon's hydro capacity, the only exception is
    the small 1.3 MW Fish Lake dam operated by ATCO/Yukon Electrical.
    That's small enough to not matter, I think.

    There is also a small 0.81 MW wind farm, its current generation is not available.
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()

    url = "http://www.yukonenergy.ca/consumption/chart_current.php?chart=current&width=420"
    response = requests_obj.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    def find_div_by_class(soup_obj, cls):
        return soup_obj.find("div", attrs={"class": cls})

    def parse_mw(text):
        try:
            return float(text[: text.index("MW")])
        except ValueError:
            return 0

    # date is specified like "Thursday, June 22, 2017"
    source_date = find_div_by_class(soup, "current_date").text

    # time is specified like "11:55 pm" or "2:25 am"
    source_time = find_div_by_class(soup, "current_time").text
    datetime_text = "{} {}".format(source_date, source_time)
    datetime_arrow = arrow.get(datetime_text, "dddd, MMMM D, YYYY h:mm A")
    datetime_datetime = arrow.get(datetime_arrow.datetime, timezone).datetime

    # generation is specified like "37.69 MW - hydro"
    hydro_div = find_div_by_class(soup, "load_hydro")
    hydro_text = hydro_div.div.text
    hydro_generation = parse_mw(hydro_text)

    hydro_cap_div = find_div_by_class(soup, "avail_hydro")
    if hydro_cap_div:
        hydro_cap_text = hydro_cap_div.div.text
        hydro_capacity = parse_mw(hydro_cap_text)
    else:
        # hydro capacity is not provided when thermal is used
        hydro_capacity = None

    thermal_div = find_div_by_class(soup, "load_thermal")
    if thermal_div.div:
        thermal_text = thermal_div.div.text
        thermal_generation = parse_mw(thermal_text)
    else:
        # thermal is not always used and when it's not used, it's not specified in HTML
        thermal_generation = 0

    data = {
        "datetime": datetime_datetime,
        "zoneKey": zone_key,
        "production": {
            "unknown": thermal_generation,
            "hydro": hydro_generation,
            # specify some sources that aren't present in Yukon as zero,
            # this allows the analyzer to better estimate CO2eq
            "coal": 0,
            "nuclear": 0,
            "geothermal": 0,
        },
        "storage": {},
        "source": "www.yukonenergy.ca",
    }

    if hydro_capacity:
        data.update({"capacity": {"hydro": hydro_capacity}})

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
