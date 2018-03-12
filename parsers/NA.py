#!/usr/bin/env python3

"""Parser for Namibia."""

import arrow
from bs4 import BeautifulSoup
from .lib.validation import validate
from PIL import Image
from pytesseract import image_to_string
import re
import requests


generation_link = 'http://www.nampower.com.na/gis/images/Gx.png'
exchanges_link = 'http://www.nampower.com.na/gis/images/Imports_Exports.png'

plant_mapping = {"Ruacana": "hydro",
                 "Van Eck": "coal",
                 "Paratus": "oil",
                 "Anixas": "oil",
                 "Solar": "solar",
                 "Wind": "wind"
                 }

exchange_mapping = {"NA->ZA": "ESKOM",
                    "NA->ZM": "ZESCO"
                    }


def get_text_from_image(link, expected_size, new_size, logger, session=None):
    """
    Gets image from link and checks expected size vs actual.
    Converts to black & white and enlarges to improve OCR accuracy.
    Performs OCR using tesseract and returns a str.
    """

    s = session or requests.Session()
    img = Image.open(s.get(link, stream=True).raw)

    if img.size != expected_size:
        if (logger):
            logger.warning("Check Namibia Scada dashboard for {} changes.".format(link),
                extras={'key': 'NA'})
        else:
            print("Check Namibia Scada dashboard for {} changes.".format(link))

    gray = img.convert('L')
    gray_enlarged = gray.resize(new_size, Image.LANCZOS)
    text = image_to_string(gray_enlarged, lang='eng')

    return text


def data_processor(text):
    """
    Takes text produced from OCR and extracts production.
    Returns a dictionary.
    """

    production = {}
    for k in plant_mapping.keys():
        pattern = re.escape(k) + r": (\d+\.\d\d)"
        try:
            val = re.search(pattern, text).group(1)
            production[plant_mapping[k]] = production.get(plant_mapping[k], 0.0)+ float(val)
        except (AttributeError, ValueError) as e:
            production[plant_mapping[k]] = None

    return production


def fetch_production(zone_key = 'NA', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_text = get_text_from_image(session=session, link=generation_link, \
                                   expected_size=(400, 245), new_size=(1000,612), \
                                   logger=logger)

    production = data_processor(raw_text)

    data = {
          'zoneKey': zone_key,
          'datetime': arrow.now('Africa/Windhoek').datetime,
          'production': production,
          'storage': {},
          'source': 'nampower.com.na'
          }

    data = validate(data, required=['hydro'])

    return data


def exchange_processor(text, exchange):
    """
    Takes text produced from OCR and extracts exchange flow.
    Returns a float or None.
    """

    utility = exchange_mapping[exchange]

    try:
        pattern = re.escape(utility) + r": -?(\d+\.\d\d)"
        val = re.search(pattern, text).group(1)
        flow = float(val)
    except (AttributeError, ValueError) as e:
        raise Exception("Exchange {} cannot be read.".format(exchange)) from e

    return flow


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    zone_key1           -- the first country code
    zone_key2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_codes = "->".join(sorted([zone_key1, zone_key2]))

    raw_text = get_text_from_image(session=session, link=exchanges_link,
                                   expected_size=(400, 195), new_size=(1120, 546), \
                                   logger=logger)

    if sorted_codes == 'NA->ZA':
        flow = exchange_processor(raw_text, 'NA->ZA')
    elif sorted_codes == 'NA->ZM':
        flow = exchange_processor(raw_text, 'NA->ZM')
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    #Import considered positive in data source.
    if flow is not None:
        flow = -1 * flow

    exchange = {'sortedZoneKeys': sorted_codes,
                'datetime': arrow.now('Africa/Windhoek').datetime,
                'netFlow': flow,
                'source': 'nampower.com.na'
                }

    return exchange


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(NA, ZA)')
    print(fetch_exchange('NA', 'ZA'))
    print('fetch_exchange(NA, ZM)')
    print(fetch_exchange('NA', 'ZM'))
