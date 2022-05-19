#!/usr/bin/env python3

"""
Real-time parser for Puerto Rico.

Fetches data from various pages embedded as an iframe at https://aeepr.com/en-us/Pages/Generaci%C3%B3n.aspx

The electricity authority is known in English as PREPA (Puerto Rico Electric Power Authority) and in Spanish as AEEPR (Autoridad de Energía Eléctrica Puerto Rico)
"""

import json
import logging
import re

# The arrow library is used to handle datetimes
import arrow

# The request library is used to fetch content through HTTP
import requests

timezone_name = "America/Puerto_Rico"
US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
HOST_PARAMETER = "?host=https://aeepr.com"
GENERATION_BREAKDOWN_URL = (
    f"{US_PROXY}/es-pr/generacion/Documents/combustibles.aspx{HOST_PARAMETER}"
)
RENEWABLES_BREAKDOWN_URL = (
    f"{US_PROXY}/es-pr/generacion/Documents/Unidades_renovables.aspx{HOST_PARAMETER}"
)
TIMESTAMP_URL = (
    f"{US_PROXY}/es-pr/generacion/Documents/CostosCombustible.aspx{HOST_PARAMETER}"
)


def extract_data(html):
    """Extracts data from the source code of an HTML page with a FusionCharts chart"""
    dataSource = re.search(r"dataSource: (\{.+\}\]\})\}\);", html).group(
        1
    )  # Extract object with data
    dataSource = re.sub(
        r",\s*\}", "}", dataSource
    )  # ,} is valid JavaScript but not valid JSON
    dataSource = json.loads(dataSource)
    sourceData = dataSource[
        "data"
    ]  # The rest of the dataSource object contains unnecessary stuff like chart theme, label, axis names etc.
    return sourceData


def convert_timestamp(
    zone_key, timestamp_string, logger: logging.Logger = logging.getLogger(__name__)
):
    """
    Converts timestamp fetched from website into timezone-aware datetime object
    Arguments:
    ----------
    timestamp_string: timestamp in the format 06/01/2020 08:40:00 AM
    """
    timestamp_string = re.sub(
        r"\s+", " ", timestamp_string
    )  # Replace double spaces with one

    logger.debug(
        f"PARSED TIMESTAMP {arrow.get(timestamp_string, 'MM/DD/YYYY HH:mm:ss A', tzinfo=timezone_name)}",
        extra={"key": zone_key},
    )
    return arrow.get(
        timestamp_string, "MM/DD/YYYY HH:mm:ss A", tzinfo=timezone_name
    ).datetime


def fetch_production(
    zone_key="US-PR",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given region."""

    global renewable_output

    if target_datetime is not None:
        raise NotImplementedError(
            "The datasource currently implemented is only real time"
        )

    r = session or requests.session()

    data = {  # To be returned as response data
        "zoneKey": zone_key,
        #'datetime': '2017-01-01T00:00:00Z',
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
        #   'storage': {
        #        'hydro': -10.0,
        #    },
        "source": "aeepr.com",
    }

    renewable_output = 0.0  # Temporarily stored here. We'll subtract solar, wind and biomass (landfill gas) from it and assume the remainder, if any,  is hydro

    # Step 1: fetch production by generation type
    # Note: seems to be rounded down (to an integer)
    # Total at the top of the page fetched in step 3 isn't rounded down, but seems to be lagging behind sometimes.
    # Difference is only minor, so for now we will IGNORE that total (instead of trying to parse the total and addding the difference to "unknown")
    res = r.get(GENERATION_BREAKDOWN_URL)

    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, GENERATION_BREAKDOWN_URL)
    )

    sourceData = extract_data(res.text)

    logger.debug(f"Raw generation breakdown: {sourceData}", extra={"key": zone_key})

    for (
        item
    ) in (
        sourceData
    ):  # Item has a label with fuel type + generation in MW, and a value with a percentage

        if item["label"] == "  MW":  # There's one empty item for some reason. Skip it.
            continue

        logger.debug(item["label"], extra={"key": zone_key})

        parsedLabel = re.search(r"^(.+?)\s+(\d+)\s+MW$", item["label"])

        category = parsedLabel.group(1)  # E.g. GAS NATURAL
        outputInMW = float(parsedLabel.group(2))

        if category == "BUNKER C" or category == "DIESEL CC" or category == "DIESEL GT":
            data["production"]["oil"] += outputInMW
        elif category == "GAS NATURAL":
            data["production"]["gas"] += outputInMW
        elif category == "CARBON":
            data["production"]["coal"] += outputInMW
        elif category == "RENOVABLES":
            renewable_output += outputInMW  # Temporarily store aggregate renewable output. We'll subtract solar, wind and biomass (landfill gas) from it and assume the remainder, if any,  is hydro
        else:
            logger.warn(
                f'Unknown energy type "{category}" is present for Puerto Rico',
                extra={"key": zone_key},
            )

        logger.info(
            f'Category "{category}" produces {outputInMW}MW', extra={"key": zone_key}
        )

    # Step 2: fetch renewable production breakdown
    # Data from this source isn't rounded. Assume renewable production not accounted for is hydro
    res = r.get(RENEWABLES_BREAKDOWN_URL)

    assert res.status_code == 200, (
        "Exception when fetching renewable production for "
        "{}: error when calling url={}".format(zone_key, RENEWABLES_BREAKDOWN_URL)
    )

    sourceData = extract_data(res.text)
    logger.debug(
        f"Raw renewable generation breakdown: {sourceData}", extra={"key": zone_key}
    )

    original_renewable_output = renewable_output  # If nothing gets subtracted renewable_output, there probably was no data on the renewables breakdown page

    logger.debug(
        f"Total (unspecified) renewable output from total generation breakdown: {original_renewable_output}MW",
        extra={"key": zone_key},
    )

    for (
        item
    ) in (
        sourceData
    ):  # Somewhat different from above, the item's label has the generation type and the item's value has generation in MW
        if item["label"] == "  ":  # There's one empty item for some reason. Skip it.
            continue

        if item["label"] == "Solar":
            data["production"]["solar"] += float(item["value"])
        elif item["label"] == "Eolica":
            data["production"]["wind"] += float(item["value"])
        elif item["label"] == "Landfill Gas":
            data["production"]["biomass"] += float(item["value"])
        else:
            logger.warn(
                f"Unknown renewable type \"{item['label']}\" is present for Puerto Rico",
                extra={"key": zone_key},
            )

        renewable_output -= float(
            item["value"]
        )  # Subtract production accounted for from the renewable output total

        logger.info(
            f"Renewable \"{item['label']}\" produces {item['value']}MW",
            extra={"key": zone_key},
        )
        logger.debug(
            f"Renewable output yet to be accounted for: {renewable_output}MW",
            extra={"key": zone_key},
        )

    logger.debug(
        "Rounding remaining renewable output to 14 decimal places to get rid of floating point errors"
    )
    renewable_output = round(renewable_output, 14)

    logger.info(
        f"Remaining renewable output not accounted for: {renewable_output}MW",
        extra={"key": zone_key},
    )

    # Assume renewable generation not accounted for is hydro - if we could fetch the other renewable generation data
    if renewable_output >= 0.0:
        if (
            original_renewable_output == renewable_output
        ):  # Nothing got subtracted for Solar, Wind or Landfill gas - so the page probably didn't contain any data. Renewable type=unknown
            logger.warning(
                f"Renewable generation breakdown page was empty, reporting unspecified renewable output ({renewable_output}MW) as 'unknown'",
                extra={"key": zone_key},
            )
            data["production"]["unknown"] += renewable_output
        else:  # Otherwise, any remaining renewable output is probably hydro
            logger.info(
                f"Assuming remaining renewable output of {renewable_output}MW is hydro",
                extra={"key": zone_key},
            )
            data["production"]["hydro"] += renewable_output
    else:
        logger.warn(
            f"Renewable generation breakdown page total is greater than total renewable output, a difference of {renewable_output}MW",
            extra={"key": zone_key},
        )

    # Step 3: fetch the timestamp, which is at the bottom of a different iframe
    # Note: there's a race condition here when requesting data very close to <hour>:10 and <hour>:40, which is when the data gets updated
    # Sometimes it's some seconds later, so we grab the timestamp from here to know the exact moment

    res = r.get(
        TIMESTAMP_URL
    )  # TODO do we know for sure the timestamp on this page gets updated *every time* the generation breakdown gets updated?

    assert (
        res.status_code == 200
    ), "Exception when fetching timestamp for " "{}: error when calling url={}".format(
        zone_key, TIMESTAMP_URL
    )

    raw_timestamp_match = re.search(
        r"Ultima Actualizaci�n:  ((?:0[1-9]|1[0-2])/(?:[0-2][0-9]|3[0-2])/2[01][0-9]{2}  [0-2][0-9]:[0-5][0-9]:[0-5][0-9] [AP]M)",
        res.text,
    )

    if raw_timestamp_match is None:
        raise Exception(f"Could not find timestamp in {res.text}")

    raw_timestamp = raw_timestamp_match.group(1)

    logger.debug(f"RAW TIMESTAMP: {raw_timestamp}", extra={"key": zone_key})

    data["datetime"] = convert_timestamp(zone_key, raw_timestamp)

    assert (
        data["production"]["oil"] > 0.0
    ), "{} is missing required generation type: oil".format(zone_key)

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
# TODO add forecast parser
#    print('fetch_generation_forecast() ->')
#    print(fetch_generation_forecast())
