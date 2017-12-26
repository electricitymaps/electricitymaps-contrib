#!/usr/bin/env python3

#Parser for Peninsular Malaysia (West Malaysia).
#This does not include the states of Sarawak and Sarawak.
#There is pumped storage in the Peninsular but no data is currently available.
#https://www.scribd.com/document/354635277/Doubling-Up-in-Malaysia-International-Water-Power

from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
from pytz import timezone
import requests

fuel_mix_url = 'https://www.gso.org.my/SystemData/FuelMix.aspx'
current_gen_url = 'https://www.gso.org.my/SystemData/CurrentGen.aspx'

fuel_mapping = {
                'ST-Coal': 'coal',
                'Hydro': 'hydro',
                'CCGT-Gas': 'gas',
                'Co-Gen': 'unknown',
                'OCGT-Gas': 'gas',
                'ST-Gas': 'gas'
                }

def get_data(session = None):
    """
    Makes two requests for the current generation total and fuel mix.
    Parses the data into raw form and reads time string associated with it.
    Checks that fuel mix sum is equal to generation total.
    Returns a tuple.
    """

    s = session or requests.Session()
    mixreq = s.get(fuel_mix_url)
    genreq = s.get(current_gen_url)
    mixsoup = BeautifulSoup(mixreq.content, 'html.parser')
    gensoup = BeautifulSoup(genreq.content, 'html.parser')

    try:
        gen_mw = gensoup.find('td', text = "MW")
        ts_tag = gen_mw.findNext('td')
        real_ts = ts_tag.text
        gen_total = float(ts_tag.findNext('td').text)

    except AttributeError:
        #No data is available between 12am-1am.
        raise ValueError('No data is currently available for Malaysia.')

    mix_header = mixsoup.find('tr', {"class": "gridheader"})
    mix_table = mix_header.find_parent("table")
    rows = mix_table.find_all('tr')
    generation_mix = {}
    for row in rows[1:]:
        cells = row.find_all('td')
        items = [ele.text.strip() for ele in cells]
        generation_mix[items[0]] = float(items[1])

    if sum(generation_mix.values()) == gen_total:
        #Fuel mix matches generation.
        return real_ts, generation_mix
    else:
        raise ValueError('Malaysia generation and fuel mix totals are not equal!')


def convert_time_str(ts):
    """Converts a unicode time string into an aware datetime object."""

    dt_naive = datetime.datetime.strptime(ts, '%m/%d/%Y %I:%M:%S %p')
    localtz = timezone('Asia/Kuala_Lumpur')
    dt_aware = localtz.localize(dt_naive)

    return dt_aware


def data_processer(rawdata):
    """
    Takes in raw data and converts it into a usable form.
    Returns a tuple.
    """

    converted_time_string = convert_time_str(rawdata[0])

    current_generation = rawdata[1]

    unmapped = []
    for gen_type in current_generation.keys():
        if gen_type not in fuel_mapping.keys():
            unmapped.append(gen_type)

    mapped_generation = [(fuel_mapping.get(gen_type, 'unknown'), val) for gen_type, val in current_generation.items()]

    generationDict = defaultdict(lambda: 0.0)

    #Sum values for duplicate keys.
    for key,val in mapped_generation:
        generationDict[key] += val

    for key in ['solar', 'wind']:
        generationDict[key] = None

    for key in ['nuclear', 'geothermal']:
        generationDict[key] = 0.0

    for gen_type in unmapped:
        print('{} is missing from the MY generation type mapping!'.format(gen_type))

    return converted_time_string, dict(generationDict)


def fetch_production(country_code = 'MY-WM', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
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
          'nuclear': 0.0,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': None,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """

    raw_data = get_data(session = None)
    clean_data = data_processer(raw_data)

    production = {
      'countryCode': country_code,
      'datetime': clean_data[0],
      'production': clean_data[1],
      'storage': {
          'hydro': None,
      },
      'source': 'gso.org.my'
    }

    return production


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
