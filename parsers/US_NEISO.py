#!/usr/bin/env python3


"""Real time parser for the New England ISO (NEISO) area."""
import arrow
from collections import defaultdict
import requests
import time

url = 'https://www.iso-ne.com/ws/wsclient'

generation_mapping = {
                      'Coal': 'coal',
                      'NaturalGas': 'gas',
                      'Wind': 'wind',
                      'Hydro': 'hydro',
                      'Nuclear': 'nuclear',
                      'Wood': 'biomass',
                      'Oil': 'oil',
                      'Refuse': 'biomass',
                      'LandfillGas': 'biomass',
                      'Solar': 'solar'
                      }

def get_json_data(session = None):
    """Fetches json data for past 2 days using a post request."""

    epoch_time = str(int(time.time()))
    ne = arrow.now('America/New_York')
    today = ne.format('MM/DD/YYYY')
    yesterday = ne.shift(days=-1).format('MM/DD/YYYY')

    postdata = {
    '_nstmp_formDate': epoch_time,
    '_nstmp_startDate': yesterday,
    '_nstmp_endDate': today,
    '_nstmp_twodays': 'false',
    '_nstmp_chartTitle': 'Fuel+Mix+Graph',
    '_nstmp_requestType': 'genfuelmix',
    '_nstmp_fuelType': 'all',
    '_nstmp_height': '250',
    '_nstmp_showtwodays': 'false'
    }

    s = session or requests.Session()

    req = s.post(url, data = postdata)
    json_data = req.json()
    raw_data = json_data[0]['data']

    return raw_data


def timestring_converter(time_string):
    """Converts ISO-8601 time strings in neiso data into aware datetime objects."""

    dt_naive = arrow.get(time_string)
    dt_aware = dt_naive.replace(tzinfo = 'America/New_York').datetime

    return dt_aware


def data_processer(raw_data):
    """
    Takes raw json data and removes unnecessary keys.
    Separates datetime key and converts to a datetime object.
    Maps generation to type and returns a list of tuples.
    """

    clean_data = []
    for datapoint in raw_data:
        keys_to_remove = ('BeginDateMs', 'Renewables')
        for k in keys_to_remove:
            datapoint.pop(k, None)

        time_string = datapoint.pop('BeginDate', None)
        dt = timestring_converter(time_string)

        production = defaultdict(lambda: 0.0)
        for k, v in datapoint.items():
            #Need to avoid duplicate keys overwriting.
            production[generation_mapping[k]] += v

        clean_data.append((dt, dict(production)))

    return sorted(clean_data)


def fetch_production(country_code = 'US-NEISO', session = None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    Return:
    A list of dictionaries in the form:
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

    get_json = get_json_data()
    points = data_processer(get_json)

    #Hydro pumped storage is included within the general hydro category.
    production_mix = []
    for item in points:
        data = {
                'countryCode': country_code,
                'datetime': item[0],
                'production': item[1],
                'storage': {
                    'hydro': None,
                },
                'source': 'iso-ne.com'
                }
        production_mix.append(data)

    return production_mix


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
