#!/usr/bin/env python3
import logging
import re
from collections import defaultdict
from typing import Optional

import arrow
import requests
from PIL import Image, ImageOps
from pytesseract import image_to_string

TIMEZONE = "Asia/Singapore"

TICKER_URL = "https://www.emcsg.com/ChartServer/blue/ticker"

SOLAR_URL = "https://www.ema.gov.sg/cmsmedia/irradiance/plot.png"

"""
Around 95% of Singapore's generation is done with combined-cycle gas turbines.

Resources:

- https://www.ema.gov.sg/Statistics.aspx particularly filtering by "Generation"
The most recent document at time of writing is
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Statistics/27RSU.pdf
It says that between January 2016 and March 2017, non-gas monthly generation breakdown has been 0.7% to 1.4% coal,
0.1% to 1.0% "petroleum products" (excluding an exceptional value of 3.9% in Nov 2016),
and 2.7% to 3.4% "other", which includes among others waste-to-energy and solar.

- Write-up of energy statistics in 2015 and first half of 2016:
https://www.ema.gov.sg/cmsmedia/Publications_and_Statistics/Publications/SES/2016/Singapore%20Energy%20Statistics%202016.pdf
(referred to as "Singapore Energy Statistics 2016" below)
It states among others "In 2015, [natural gas] accounted for about 95% of fuel mix,
comparable with that recorded in 2014. Petroleum products, mainly in the form of diesel and fuel oil,
made up 0.7% of the fuel mix. Other energy products (e.g. municipal waste, coal and biomass)
accounted for 2.9% while the remaining 1.2% was from coal", and that steam turbines in Singapore
"typically run on fuel oil and diesel'

The real-time information on EMCSG website includes data for three categories: "CCGT/COGEN/TRIGEN", "GT", and "ST".
I take these to mean combined-cycle gas turbines/co-generation/tri-generation,
single-cycle gas turbines (following the Energy Statistics 2016 pg 24), and steam turbines respectively.
There is no real-time information on fuel for steam turbines.

For Electricity Map, we map CCGT and GT to gas, and ST to "unknown".

The Energy Market Authority estimates current solar production and publishes it at
https://www.ema.gov.sg/solarmap.aspx

There exists an interconnection to Malaysia, it is implemented in MY_WM.py.
"""

TYPE_MAPPINGS = {"CCGT/COGEN/TRIGEN": "gas", "GT": "gas", "ST": "unknown"}


def get_solar(session, logger) -> Optional[float]:
    """
    Fetches a graphic showing estimated solar production data.
    Uses OCR (tesseract) to extract MW value.
    """

    url = SOLAR_URL
    solar_image = Image.open(session.get(url, stream=True).raw)

    solar_mw = __detect_output_from_solar_image(solar_image, logger)
    solar_dt = __detect_datetime_from_solar_image(solar_image, logger)

    singapore_dt = arrow.now("Asia/Singapore")
    diff = singapore_dt - solar_dt

    # Need to be sure we don't get old data if image stops updating.
    if diff.total_seconds() > 3600:
        msg = (
            "Singapore solar data is too old to use, " "parsed data timestamp was {}."
        ).format(solar_dt)
        logger.warning(msg, extra={"key": "SG"})
        return None

    return solar_mw


def parse_megawatt_value(val) -> int:
    """Turns values like "5,156MW" and "26MW" into 5156 and 26 respectively."""
    return int(val.replace(",", "").replace("MW", ""))


def parse_percent(val) -> float:
    """Turns values like "97.92%" into 0.9792."""
    return float(val.replace("%", "")) / 100


def parse_price(price_str) -> float:
    """Turns values like "$70.57/MWh" into 70.57"""

    return float(price_str.replace("$", "").replace("/MWh", ""))


def find_first_list_item_by_key_value(l, filter_key, filter_value, sought_key):
    """
    Parses a common pattern in Singapore JSON response format. Examples:

    [d['Value'] for d in energy_section if d['Label'] == 'Demand'][0]
        => find_first_list_item_by_key_value(energy_section, 'Label', 'Demand', 'Value')

    [section['SectionData'] for section in sections if section['Name'] == 'Energy'][0]
        => find_first_list_item_by_key_value(sections, 'Name', 'Energy', 'SectionData')

    [d['Value'] for d in energy_section if d['Label'] == 'USEP'][0]
        => find_first_list_item_by_key_value(energy_section, 'Label', 'USEP', 'Value')
    """

    return [
        list_item[sought_key]
        for list_item in l
        if list_item[filter_key] == filter_value
    ][0]


def sg_period_to_hour(period_str) -> float:
    """
    Singapore electricity markets are split into 48 periods.
    Period 1 starts at 00:00 Singapore time, Period 9 starts at 04:00.
    Returns hours since midnight, possibly with 0.5 to indicate 30 minutes.
    """
    return (float(period_str) - 1) / 2.0


def sg_data_to_datetime(data):
    data_date = data["Date"]
    data_time = sg_period_to_hour(data["Period"])
    date_arrow = arrow.get(data_date, "DD MMM YYYY")
    datetime_arrow = date_arrow.shift(hours=data_time)
    data_datetime = arrow.get(datetime_arrow.datetime, TIMEZONE).datetime
    return data_datetime


def fetch_production(
    zone_key="SG",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of Singapore."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()

    response = requests_obj.get(TICKER_URL)
    data = response.json()

    sections = data["Sections"]

    energy_section = find_first_list_item_by_key_value(
        sections, "Name", "Energy", "SectionData"
    )

    demand_str = find_first_list_item_by_key_value(
        energy_section, "Label", "Demand", "Value"
    )
    demand = parse_megawatt_value(demand_str)
    system_loss_str = find_first_list_item_by_key_value(
        energy_section, "Label", "System Loss", "Value"
    )
    system_loss = parse_megawatt_value(system_loss_str)

    generation = demand + system_loss

    mix_section = find_first_list_item_by_key_value(
        sections, "Name", "Generator Type Share", "SectionData"
    )

    gen_types = {
        gen_type["Label"]: parse_percent(gen_type["Value"]) for gen_type in mix_section
    }

    generation_by_type = defaultdict(float)  # this dictionary will default keys to 0.0

    for gen_type, gen_percent in gen_types.items():
        gen_mw = gen_percent * generation
        mapped_type = TYPE_MAPPINGS.get(gen_type, None)

        if mapped_type:
            generation_by_type[TYPE_MAPPINGS[gen_type]] += gen_mw

        else:
            # unrecognized - log it, then add into unknown
            msg = (
                'Singapore has unrecognized generation type "{}" '
                "with production share {}%"
            ).format(gen_type, gen_percent)
            logger.warning(msg)
            generation_by_type["unknown"] += gen_mw

    generation_by_type["solar"] = get_solar(requests_obj, logger)

    # some generation methods that are not used in Singapore
    generation_by_type.update({"nuclear": 0, "wind": 0, "hydro": 0})

    return {
        "datetime": sg_data_to_datetime(data),
        "zoneKey": zone_key,
        "production": generation_by_type,
        "storage": {},  # there is no known electricity storage in Singapore
        "source": "emcsg.com, ema.gov.sg",
    }


def fetch_price(zone_key="SG", session=None, target_datetime=None, logger=None) -> dict:
    """
    Requests the most recent known power prices in Singapore (USEP).

    See https://www.emcsg.com/marketdata/guidetoprices for details of what different prices in the data source mean.
    We use USEP here: "The Uniform Singapore Energy Price (USEP) is the uniform price of energy
    that applies for settlement purposes for all energy injections or withdrawals that are deemed to occur
    at the Singapore hub. It is the weighted-average of the nodal prices at all off-take nodes in each half hour."

    There are also price forecasts for future prices at https://www.emcsg.com/marketdata/priceinformation
    that appears to extend to end of day in Singapore, so up to 24 hours into the future,
    however we don't currently use this.
    """
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()
    response = requests_obj.get(TICKER_URL)
    data = response.json()

    sections = data["Sections"]

    energy_section = find_first_list_item_by_key_value(
        sections, "Name", "Energy", "SectionData"
    )

    price_str = find_first_list_item_by_key_value(
        energy_section, "Label", "USEP", "Value"
    )
    price = parse_price(price_str)

    return {
        "zoneKey": zone_key,
        "datetime": sg_data_to_datetime(data),
        "currency": "SGD",
        "price": price,
        "source": "emcsg.com",
    }


def __detect_datetime_from_solar_image(solar_image, logger):
    w, h = solar_image.size
    crop_left = int(w * 0.75)
    crop_top = int(h * 0.87)
    crop_right = int(w * 0.93)
    crop_bottom = int(h * 0.92)
    time_img = solar_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    processed_img = __preprocess_image_for_ocr(time_img)
    text = image_to_string(
        processed_img,
        lang="eng",
        config='--psm 7 -c tessedit_char_whitelist="0123456789:- "',
    )

    try:
        time_pattern = r"\d+-\d+-\d+\s+\d+:\d+"
        time_string = re.search(time_pattern, text, re.MULTILINE).group(0)
    except AttributeError:
        msg = "Unable to get values for SG solar from OCR text: {}".format(text)
        logger.warning(msg, extra={"key": "SG"})
        return None

    solar_dt = arrow.get(time_string).replace(tzinfo="Asia/Singapore")
    return solar_dt


def __detect_output_from_solar_image(solar_image, logger):
    w, h = solar_image.size
    crop_left = int(w * 0.65)
    crop_top = int(h * 0.74)
    crop_right = int(w * 0.93)
    crop_bottom = int(h * 0.80)
    output_img = solar_image.crop((crop_left, crop_top, crop_right, crop_bottom))
    processed_img = __preprocess_image_for_ocr(output_img)
    text = image_to_string(processed_img, lang="eng", config="--psm 7")

    try:
        pattern = r"Est. PV Output: (.*)MWac"
        val = re.search(pattern, text, re.MULTILINE).group(1)
    except AttributeError:
        msg = "Unable to get values for SG solar from OCR text: {}".format(text)
        logger.warning(msg, extra={"key": "SG"})
        return None

    # At night format changes from 0.00 to 0
    # tesseract cannot distinguish singular 0 and O in font provided by image.
    # This try/except will make sure no invalid data is returned.
    try:
        solar_mw = float(val)
    except ValueError:
        if val == "O":
            solar_mw = 0.0
        else:
            msg = "Singapore solar data is unreadable - got {}.".format(val)
            logger.warning(msg, extra={"key": "SG"})
            return None

    return solar_mw


def __preprocess_image_for_ocr(img):
    """
    Perform a number of image pre-processing recommendations to improve success of character recognition.

    :param img: the image to be processed
    :return: pre-processed image, optimized for optical character recognition (OCR)
    """
    # https://tesseract-ocr.github.io/tessdoc/ImproveQuality#inverting-images
    inverted_img = ImageOps.invert(
        img
    )  # assumes black background of Singapore solar output image
    dark_text_on_light_bg = inverted_img.convert("L")

    # https://tesseract-ocr.github.io/tessdoc/ImproveQuality#missing-borders
    img_with_border = ImageOps.expand(dark_text_on_light_bg, border=2)

    return img_with_border


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print('fetch_price("SG") ->')
    print(fetch_price("SG"))
