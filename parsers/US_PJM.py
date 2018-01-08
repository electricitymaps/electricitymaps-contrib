#!/usr/bin/env python3

"""Parser for the PJM area of the United States."""

import arrow
from bs4 import BeautifulSoup
import demjson
import re
import requests


url = 'http://www.pjm.com/markets-and-operations.aspx'

mapping = {
            'Coal': 'coal',
            'Gas': 'gas',
            'Hydro': 'hydro',
            'Multiple Fuels': 'unknown',
            'Nuclear': 'nuclear',
            'Oil': 'oil',
            'Other': 'unknown',
            'Other Renewables': 'unknown',
            'Solar': 'solar',
            'Wind': 'wind'
            }


def extract_data(session = None):
    """
    Makes a request to the PJM data url.
    Finds timestamp of current data and converts into a useful form.
    Finds generation data inside script tag.
    Returns a tuple of generation data and datetime.
    """

    s = session or requests.Session()
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')

    try:
        time_div = soup.find("div", id="asOfDate").text
    except AttributeError:
        raise LookupError('No data is available for US-PJM.')

    time_pattern = re.compile(r"""(\d{1,2}     #Hour can be 1/2 digits.
                                   :           #Separator.
                                   \d{2})\s    #Minutes must be 2 digits with a space after.
                                   (a.m.|p.m.) #Either am or pm allowed.""", re.X)

    latest_time = re.search(time_pattern, time_div)

    time_data = latest_time.group(1).split(":")
    am_or_pm = latest_time.group(2)
    hour = int(time_data[0])
    minute = int(time_data[1])

    #Time format used by PJM is slightly unusual and needs to be converted so arrow can use it.
    if am_or_pm == "p.m." and hour != 12:
        #Time needs to be in 24hr format
        hour += 12
    elif am_or_pm == "a.m." and hour == 12:
        #Midnight is 12 a.m.
        hour = 0

    arr_dt = arrow.now('America/New_York').replace(hour=hour, minute=minute)
    future_check = arrow.now('America/New_York')

    if arr_dt > future_check:
        #Generation mix lags 1-2hrs behind present.
        #This check prevents data near midnight being given the wrong date.
        arr_dt.shift(days=-1)

    dt = arr_dt.floor('minute').datetime

    generation_mix_div = soup.find("div", id="rtschartallfuelspjmGenFuelM_container")
    generation_mix_script = generation_mix_div.next_sibling

    pattern = r'series: \[(.*)\]'
    script_data = re.search(pattern, str(generation_mix_script)).group(1)

    #demjson is required because script data is javascript not valid json.
    raw_data = demjson.decode(script_data)
    data = raw_data["data"]

    return data, dt


def data_processer(data):
    """
    Takes a list of dictionaries and extracts generation type and value from each.
    Returns a dictionary.
    """

    production = {}
    for point in data:
        gen_type = mapping[point['name']]
        gen_value = float(point['y'])
        production[gen_type] = production.get(gen_type, 0.0) + gen_value

    return production


def fetch_production(country_code = 'US-PJM', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
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

    extracted = extract_data(session = None)
    production = data_processer(extracted[0])

    datapoint = {
      'countryCode': country_code,
      'datetime': extracted[1],
      'production': production,
      'storage': {'hydro': None, 'battery': None},
      'source': 'pjm.com'
    }

    return datapoint


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
