#!/usr/bin/env python3

"""Parser for the PJM area of the United States."""

import arrow
from bs4 import BeautifulSoup
import demjson
import re
import requests


# Used for both production and price data.
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

exchange_mapping = {
                    'nyiso': 'NYIS|NYIS',
                    'neptune': 'NEPTUNE|SAYR',
                    'linden': 'LINDENVFT|LINDEN',
                    'hudson': 'HUDSONTP|HTP',
                    'miso': 'miso',
                    'ohio valley': 'DEOK|OVEC',
                    'louisville': 'SOUTHIMP|LGEE',
                    'tennessee valley': 'SOUTHIMP|TVA',
                    'cpl west': 'SOUTHIMP|CPLW',
                    'duke': 'SOUTHIMP|DUKE',
                    'cpl east': 'SOUTHIMP|CPLE'
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


def get_exchange_data(interface, session = None):
    """
    This function can fetch 5min data for any PJM interface in the current day.
    Extracts load and timestamp data from html source then joins them together.
    Returns a list of tuples.
    """

    base_url = 'http://www.pjm.com/Charts/InterfaceChart.aspx?open='
    url = base_url + exchange_mapping[interface]

    s = session or requests.Session()
    req = s.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')

    scripts = soup.find("script", {"type": "text/javascript",
                                   "src": "/assets/js/Highcharts/HighCharts/highcharts.js"})

    exchange_script = scripts.find_next_sibling("script")

    load_pattern = r'var load = (\[(.*)\])'
    load = re.search(load_pattern, str(exchange_script)).group(1)
    load_vals = demjson.decode(load)[0]

    # Occasionally load_vals contains a null at the end of the list which must be caught.
    actual_load = [float(val) for val in load_vals if val is not None]

    time_pattern = r'var timeArray = (\[(.*)\])'
    time_array = re.search(time_pattern, str(exchange_script)).group(1)
    time_vals = demjson.decode(time_array)

    flows = zip(actual_load, time_vals)

    arr_date = arrow.now('America/New_York').floor('day')

    converted_flows = []
    for flow in flows:
        arr_time = arrow.get(flow[1], 'h:mm A')
        arr_dt = arr_date.replace(hour=arr_time.hour, minute=arr_time.minute).datetime
        converted_flow = (flow[0], arr_dt)
        converted_flows.append(converted_flow)

    return converted_flows


def combine_NY_exchanges():
    """
    Combination function for the 4 New York interfaces.
    Timestamps are checked to ensure correct combination.
    Returns a list of tuples.
    """

    nyiso = get_exchange_data('nyiso', session = None)
    neptune = get_exchange_data('neptune', session = None)
    linden = get_exchange_data('linden', session = None)
    hudson = get_exchange_data('hudson', session = None)

    combined_flows = zip(nyiso, neptune, linden, hudson)

    flows = []
    for datapoint in combined_flows:
        total = sum([n[0] for n in datapoint])
        stamps = [n[1] for n in datapoint]

        # Data quality check to make sure timestamps all match.
        if len(set(stamps)) == 1:
            dt = stamps[0]
        else:
            # Drop bad datapoint and move to next.
            continue

        flows.append((total, dt))

    return flows


def fetch_exchange(country_code1, country_code2, session = None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    country_code1           -- the first country code
    country_code2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    # PJM reports exports as negative.
    sortedcodes = '->'.join(sorted([country_code1, country_code2]))

    if sortedcodes == 'US-NY->US-PJM':
        flows = combine_NY_exchanges()
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    exchanges = []
    for flow in flows:
        exchange = {
          'sortedCountryCodes': sortedcodes,
          'datetime': flow[1],
          'netFlow': flow[0],
          'source': 'pjm.com'
        }
        exchanges.append(exchange)

    return exchanges


def fetch_price(country_code = 'US-PJM', session = None):
    """Requests the last known power price of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """

    s = session or requests.Session()
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')

    price_tag = soup.find("span", class_="rtolmpico")
    price_data = price_tag.find_next("h2")
    price_string = price_data.text.split("$")[1]
    price = float(price_string)

    dt = arrow.now('America/New_York').floor('second').datetime

    data = {
        'countryCode': country_code,
        'currency': 'USD',
        'datetime': dt,
        'price': price,
        'source': 'pjm.com',
        }

    return data


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(US-NY, US-PJM) ->')
    print(fetch_exchange('US-NY', 'US-PJM'))
    print('fetch_price() ->')
    print(fetch_price())
