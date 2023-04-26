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

"""
Two more endpoints, not needed here. Contain status of power plants, and 24h history of frequency and generation sum.
/es-pr/generacion/Documents/DataJS/dataGraph.js"
/es-pr/generacion/Documents/DataJS/dataUnitStatus.js"
"""

VAILDATION_THRESHOLD_PERCENT = 5.0

# Source data identifiers -> Production types. See also comments at oil/gas validation
SRC_POWER_TYPE_TO_PRODUCTION_TYPE = {
    # fossil
    "Turbina de Gas": "gas",
    "COGEN": "",  # see get_production_type_from_site()
    "Vapor": "oil",
    "Ciclo Combinado": "gas",
    # renewables
    "Hidroelectricas": "hydro",
    "Wind": "wind",
    "Solar": "solar",
    "Landfill": "biomass",
}


def get_production_type_from_site(json_site):

    if json_site["Type"] == "Renovable":
        # Renovable-Type has specific type in 'Desc' attribute
        return SRC_POWER_TYPE_TO_PRODUCTION_TYPE[json_site["Desc"]]
    elif json_site["Type"] == "COGEN":
        # "Cogeneradoras" (cogeneration units),  there are two active:
        #   Ecoelectrica = gas (https://www.power-technology.com/marketdata/power-plant-profile-ecoelectrica-penuelas-power-plant-puerto-rico/)
        #   AES = coal (https://www.power-technology.com/marketdata/power-plant-profile-guayama-coal-fired-power-plant-puerto-rico/)
        if json_site["Desc"] == "Ecoelectrica":
            return "gas"  # https://www.eia.gov/state/analysis.php?sid=RQ
        elif json_site["Desc"] == "AES":
            return "coal"
    elif json_site["Type"] == "Vapor":
        if json_site["Desc"] == "Costa Sur":
            return "gas"  # https://www.eia.gov/state/analysis.php?sid=RQ

    if json_site["Type"] in SRC_POWER_TYPE_TO_PRODUCTION_TYPE:
        return SRC_POWER_TYPE_TO_PRODUCTION_TYPE[json_site["Type"]]
    else:
        return None


def parse_datetime(
    input_data: str, zone_key: str, logger: Logger = getLogger(__name__)
):
    """
    Parses the timezone-aware datetime object from the time specified in the .js file

    Expected format in file:
    const dataFechaAcualizado = '4/25/2023' + ' 3:06:05 PM';
    Expected format as string:
    M/DD/YYYY h:mm:ss A

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
    date_fmt = "M/DD/YYYY h:mm:ss A"

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


def validate_fuel_type(
    fuel_type: str,
    production_data,
    total_production: int,
    expected_perc: float,
    logger: Logger = getLogger(__name__),
):
    """
    Validate the source ratio of different fuel types. The data source gives us the ratio of
    oil/gas/coal/diesel/renewables, and we accumulate the production over each plant. This method
    validates whether the accumulated production matches the given total ratio.

    Arguments:
    ----------
    fuel_type: string identifier of fuel type in the data source
    production_data: the production data we create accumulated over all production sites
    total_production: total production given by data source
    expected_perc: Expected percent of this fuel type given by the data source
    ----------
    Returns:
    ----------
    The difference of expected and actual fuelType ratio in percent.
    """

    if fuel_type == "Bunker":
        acc_production_perc = (
            100.0 * production_data["production"]["oil"] / total_production
        )
    elif fuel_type == "Diesel":
        acc_production_perc = 0.0 / total_production  # We do not have a Diesel source.
    elif fuel_type == "LNG":
        acc_production_perc = (
            100.0 * production_data["production"]["gas"] / total_production
        )
    elif fuel_type == "Coal":
        acc_production_perc = (
            100.0 * production_data["production"]["coal"] / total_production
        )
    elif fuel_type == "Renew":
        acc_production_perc = (
            100.0
            * (
                production_data["production"]["biomass"]
                + production_data["production"]["hydro"]
                + production_data["production"]["solar"]
                + production_data["production"]["wind"]
                + production_data["production"]["geothermal"]
            )
            / total_production
        )

    return abs(expected_perc - acc_production_perc)


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
    fetch_dt = parse_datetime(data_js, zone_key)
    if fetch_dt is None:
        raise ParserException(
            parser="US_PREPA.py",
            message="The datetime could not be parsed from given data source.",
        )

    data_fuel_cost = parse_js_block_to_json(data_js, "dataFuelCost", zone_key)
    data_by_fuel = parse_js_block_to_json(data_js, "dataByFuel", zone_key)
    data_metrics = parse_js_block_to_json(data_js, "dataMetrics", zone_key)
    data_load_per_site = parse_js_block_to_json(data_js, "dataLoadPerSite", zone_key)

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

    # logger.debug(f"Raw generation breakdown: {data_load_per_site}", extra={"key": zone_key})
    # logger.debug(f"Past 24h metrics: {data_metrics}", extra={"key": zone_key})
    # logger.debug(f"Breakdown by fuel type: {data_by_fuel}", extra={"key": zone_key})
    # logger.debug(f"Fuel cost breakdown: {data_fuel_cost}", extra={"key": zone_key})

    # DataByFuel splits source already in 5 types, but do not further specify sub-type (e.g., renewables)
    # Therefore, accumulate data from each site, and make sanity checks at the end
    total_sites_mw = 0
    for site_info in data_load_per_site:

        production_type = get_production_type_from_site(site_info)
        if production_type is None:
            logger.warning(
                f"Cannot parse production type {site_info['Type']} from site. Putting it into 'unkown'."
            )
            production_type = "unknown"

        output_mw = site_info["SiteTotal"]
        total_sites_mw += output_mw

        site_desc = site_info["Desc"]
        logger.debug(
            f"Adding source {site_desc} to type {production_type} - generating {output_mw} MW.",
            extra={"key": zone_key},
        )

        data["production"][production_type] += output_mw

        # Sanity check: iterate over units of this plant and make sure they accumuate close to SiteTotal
        unit_sum_mw = 0
        for unit in site_info["units"]:
            unit_sum_mw += unit["MW"]
        # All information in rounded to integers. Give some leeway when calculating sum.
        if abs(unit_sum_mw - output_mw) > len(site_info["units"]):
            logger.warning(
                f"Sum of production units of site {site_info['Index']} ({unit_sum_mw} MW) "
                f"does not match given SiteTotal ({output_mw} MW) in zone {zone_key} at {fetch_dt}."
            )

    # Sanity check: compare sum over power sources with given total generation
    if abs(total_sites_mw - data_metrics_total_gen) > len(data_load_per_site):
        logger.warning(
            f"Sum of production of all sites sites in zone {zone_key} at {fetch_dt} "
            f"is {total_sites_mw} MW, but given total production is {data_metrics_total_gen} MW."
        )

    """
    Some of the plants in PR are capable of combusting both gas and oil. Currently, PR is in the process of 
    transforming some of the power plants from oil driven to gas or even hybrid. The data does not contain 
    information, on which mode a plant is currently operating on. However, we know the production
    percentage of oil and gas over PR in total. Therefore, some of the extracted mappings plant -> fuelType
    be wrong. Here, we compensate for that error, by taking the given ratios (%) of oil/gas in the data source,
    and adjust the oil/gas amount accordingly to fulfill this ratio.
    Report of a power plant operating on both modes:
    https://energia.pr.gov/wp-content/uploads/sites/7/2022/06/SL-015976.SJ_San-Juan-IE-Report_-Draft-13Nov2020.pdf
    """

    # Sanity check: Compare src % of oil and gas
    valid = (
        validate_fuel_type(
            "Bunker",
            data,
            data_metrics_total_gen,
            get_field_value(data_by_fuel, ("fuel", "Bunker"), "value"),
        )
        < VAILDATION_THRESHOLD_PERCENT
        and validate_fuel_type(
            "LNG",
            data,
            data_metrics_total_gen,
            get_field_value(data_by_fuel, ("fuel", "LNG"), "value"),
        )
        < VAILDATION_THRESHOLD_PERCENT
    )

    if not valid:
        rel_gas_target = get_field_value(data_by_fuel, ("fuel", "LNG"), "value") / 100.0
        current_gas = data["production"]["gas"] / data_metrics_total_gen
        # difference to compensate
        add_gas = rel_gas_target - current_gas
        logger.warning(
            f"Correcting gas ratio by {add_gas * 100.0}%, inverse to oil ratio."
        )

        data["production"]["gas"] += add_gas * data_metrics_total_gen
        data["production"]["oil"] -= add_gas * data_metrics_total_gen

    # Validate again and make sure everything within bounds now.
    for fuel_type in data_by_fuel:
        fuel_type_identifier = fuel_type["fuel"]
        fuel_type_value_percent = fuel_type["value"]
        err_percent = validate_fuel_type(
            fuel_type_identifier, data, data_metrics_total_gen, fuel_type["value"]
        )
        if err_percent >= VAILDATION_THRESHOLD_PERCENT:
            logger.warning(
                f"Sum of computed production type for {fuel_type_identifier} is {err_percent}% "
                f"of expected value ({fuel_type_value_percent}%)."
            )

    # with open(fetch_dt.strftime("%Y-%m-%d-%H-%M") + ".txt", "w") as text_file:
    #     text_file.write(data_js) # TODO debug out to file

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
