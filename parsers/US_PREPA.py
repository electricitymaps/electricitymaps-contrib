#!/usr/bin/env python3

"""
Real-time parser for Puerto Rico.

Fetches data from javascript sources used from the dashboard at https://aeepr.com/es-pr/Paginas/NewGen/dashboard.aspx

The electricity authority is known in English as PREPA (Puerto Rico Electric Power Authority) and in Spanish as AEEPR (Autoridad de Energía Eléctrica Puerto Rico)
"""

import json
import re
from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

import arrow
from requests import Response, Session

from parsers.lib.exceptions import ParserException

timezone_name = "America/Puerto_Rico"
US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "?host=https://aeepr.com"

GENERATION_BREAKDOWN_URL = (
    f"https://aeepr.com/es-pr/generacion/Documents/DataJS/dataSource.js"
    # f"{US_PROXY}/es-pr/generacion/Documents/DataJS/dataSource.js{HOST_PARAMETER}"
)

# renewable source data identifiers -> Production types
RENEWABLE_SRC_TYPE_TO_PRODUCTION_TYPE = {
    # renewables
    "Hidroelectricas": "hydro",
    "Wind": "wind",
    "Solar": "solar",
    "Landfill": "biomass",
}


def get_site_renewable_type(site_info, logger):
    """
    Get the renewable power type from the site info.
    """
    # Type could be 'Hidroelectricas'
    if site_info["Type"] in RENEWABLE_SRC_TYPE_TO_PRODUCTION_TYPE.keys():
        return RENEWABLE_SRC_TYPE_TO_PRODUCTION_TYPE[site_info["Type"]]

    # On other cases, the type is just 'Renovable'
    if site_info["Type"] == "Renovable":
        # Renovable-Type has specific type in 'Desc' attribute (solar, wind...)
        type_desc = site_info["Desc"]

        if type_desc not in RENEWABLE_SRC_TYPE_TO_PRODUCTION_TYPE.keys():
            logger.warn(f"Unknown renewable type in data: {type_desc}, skipping...")
            return None

        return RENEWABLE_SRC_TYPE_TO_PRODUCTION_TYPE[type_desc]
    else:
        return None


def parse_datetime(input_data: str, zone_key: str, logger: Logger):
    """
    Parses the timezone-aware datetime object from the time specified in the .js file

    Expected format in file:
    const dataFechaAcualizado = '4/25/2023' + ' 3:06:05 PM';
    Expected format as string:
    M/D/YYYY h:mm:ss A

    Arguments:
    ----------
    input_data: The input .js file as string
    zone_key: the two letter zone from the map
    ----------
    Returns:
    ----------
    The datetime specified in the file as outlined above. None if could not be parsed.
    """

    # in file: const dataFechaAcualizado = '4/25/2023' + ' 3:06:05 PM';
    date_matches = re.search(
        r"\Aconst\sdataFechaAcualizado\s*=\s*'(.*)'\s\+\s'(.*)';", input_data
    )
    date_fmt = "M/D/YYYY h:mm:ss A"

    date_str = "".join(date_matches.group(1, 2))
    logger.debug(
        f"Found timestamp string: {date_str}",
        extra={"key": zone_key},
    )

    try:
        date_obj = arrow.get(date_str, date_fmt, tzinfo=timezone_name).datetime
        logger.debug(
            f"Parsed time: {date_obj}",
            extra={"key": zone_key},
        )
        return date_obj

    except arrow.parser.ParserError as e:
        logger.warn(f"Could not parse timestamp {date_str} to format {date_fmt}." "{e}")
        return None


def parse_js_block_to_json(
    input_data: str,
    identifier: str,
    zone_key: str,
    logger: Logger = getLogger(__name__),
):
    """
    Parses a JavaScript Object Literal block in the .js file into a JSON object.

    Expected format in file:
    const identifier = {JSOL-STYLE};

    Arguments:
    ----------
    input_data: The input .js file as string
    identifier: The const identifier to look for in the file
    zone_key: the two letter zone from the map
    ----------
    Returns:
    ----------
    The JSON object if successfully parsed, otherwise None.
    """

    # create regex expression to extract block and extract it
    regex = r"const\s" + identifier + r"\s*=\s*(.*?);"
    id_matches = re.search(regex, input_data, re.DOTALL)
    if id_matches is None:
        logger.warning(f"Failed to parse data block identifier {identifier}.")
        return None
    dict_match = id_matches.group(1)

    # transform the JSOL to JSON.
    # add '' to keys
    dict_match = re.sub(r"(\w+):", r"'\g<1>':", dict_match)
    # replace all ' with "
    dict_match = re.sub("'", '"', dict_match)
    # remove trailing commas at end of object lists
    dict_match = re.sub(r"\,([\s]*[\}|\]])", r"\g<1>", dict_match)

    try:
        json_obj = json.loads(dict_match)
        return json_obj
    except json.decoder.JSONDecodeError as e:
        logger.warning(f"Failed to parse for JSOL to JSON converted string. {e}")
        return None


def get_field_value(in_json, kv_access: tuple, get_id: str):
    """
    Get a specific attribute value of a json list.
    Serves as helper function.

    Arguments:
    ----------
    in_json: The JSON object having a list of sub-objects
    kv_access: (key, value) pair to look for in each sub-object
    get_id: Identifier whose value should be returned

    """

    for sub_obj in in_json:
        if sub_obj[kv_access[0]] == kv_access[1]:
            return sub_obj[get_id]

    return None


def fetch_production(
    zone_key: str = "US-PR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given region."""

    if target_datetime is not None:
        raise NotImplementedError(
            "The datasource currently implemented is only real time"
        )

    r = session or Session()

    # Fetch production by generation type
    res: Response = r.get(GENERATION_BREAKDOWN_URL)
    assert res.ok, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, GENERATION_BREAKDOWN_URL)
    )

    data_js = res.text

    # parse datetime contained in the received .js file
    fetch_dt = parse_datetime(data_js, zone_key, logger)
    if fetch_dt is None:
        raise ParserException(
            parser="US_PREPA.py",
            message="The datetime could not be parsed from given data source.",
        )

    data_fuel_cost = parse_js_block_to_json(data_js, "dataFuelCost", zone_key)
    data_by_fuel = parse_js_block_to_json(data_js, "dataByFuel", zone_key)
    data_metrics = parse_js_block_to_json(data_js, "dataMetrics", zone_key)
    data_load_per_site = parse_js_block_to_json(data_js, "dataLoadPerSite", zone_key)

    # Total generation
    data_metrics_total_gen = get_field_value(
        data_metrics, ("Desc", "Total de Generación"), "value"
    )

    data = {
        "zoneKey": zone_key,
        "datetime": fetch_dt,
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "nuclear": 0.0,
            "oil": 0.0,
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "unknown": 0.0,
        },
        "source": "aeepr.com",
    }

    """
    Some of the plants in PR are capable of combusting both gas and oil. Currently, PR is in the process of 
    transforming some of the power plants from oil driven to gas or even hybrid. The data does not contain 
    information, on which mode a plant is currently operating on. However, we know the production
    percentage of oil and gas over PR in total. Therefore, we infer fossil sources based on given ratios (%)
    from the data source.
    Report of a power plant operating on both modes:
    https://energia.pr.gov/wp-content/uploads/sites/7/2022/06/SL-015976.SJ_San-Juan-IE-Report_-Draft-13Nov2020.pdf

    Renewables are parsed from the precise sources to get their power type.
    """

    total_sites_mw = 0
    # For each site, if renewable, account for it in data field.
    for site_info in data_load_per_site:

        # production_type = get_production_type_from_site(site_info)
        output_mw = site_info["SiteTotal"]
        site_desc = site_info["Desc"]
        total_sites_mw += output_mw

        renewable_production_type = get_site_renewable_type(site_info, logger)
        if renewable_production_type is None:
            continue  # site is not renewable

        logger.debug(
            f"Adding source {site_desc} to type {renewable_production_type} - generating {output_mw} MW.",
            extra={"key": zone_key},
        )
        data["production"][renewable_production_type] += output_mw

    # Get % production of fossile sources
    # our 'oil' is oil (Bunker) and diesel
    oil_perc = get_field_value(
        data_by_fuel, ("fuel", "Bunker"), "value"
    ) + get_field_value(data_by_fuel, ("fuel", "Diesel"), "value")
    gas_perc = get_field_value(data_by_fuel, ("fuel", "LNG"), "value")
    coal_perc = get_field_value(data_by_fuel, ("fuel", "Coal"), "value")

    oil_mw = data_metrics_total_gen * oil_perc / 100.0
    gas_mw = data_metrics_total_gen * gas_perc / 100.0
    coal_mw = data_metrics_total_gen * coal_perc / 100.0

    data["production"]["oil"] = oil_mw
    data["production"]["gas"] = gas_mw
    data["production"]["coal"] = coal_mw

    logger.debug(
        f"Infer type 'oil' from ratio table ({oil_perc}%) - generating {oil_mw} MW.",
        extra={"key": zone_key},
    )
    logger.debug(
        f"Infer type 'gas' from ratio table ({gas_perc}%) - generating {gas_mw} MW.",
        extra={"key": zone_key},
    )
    logger.debug(
        f"Infer type 'gas' from ratio table ({coal_perc}%) - generating {coal_mw} MW.",
        extra={"key": zone_key},
    )

    # Sanity check: compare sum over power sources with given total generation.
    # Compare it with number of sites since these are round off errors.
    if abs(total_sites_mw - data_metrics_total_gen) > len(data_load_per_site):
        logger.warning(
            f"Sum of production of all sites in zone {zone_key} at {fetch_dt} "
            f"is {total_sites_mw} MW, but given total production is {data_metrics_total_gen} MW."
        )

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
