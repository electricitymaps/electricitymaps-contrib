#!/usr/bin/env python3

"""Parser for the MISO area of the United States."""

import json
import requests

mix_url = 'https://api.misoenergy.org/MISORTWDDataBroker/DataBrokerServices.asmx?messageType=getfuelmix&returnType=json'

mapping = {'Coal': 'coal',
           'Natural Gas': 'gas',
           'Nuclear': 'nuclear',
           'Wind': 'wind',
           'Other': 'unknown'}


def get_json_data(session = None):
    """Returns 5 minute generation data in json format."""

    s = session or requests.session()
    json_data = s.get(mix_url).json()

    return json_data


def data_processer(json_data):
    """why not how"""

    generation = json_data['Fuel']['Type']

    production = {}
    for fuel in generation:
        try:
            k = mapping[fuel['CATEGORY']]
        except KeyError as e:
            print("Key \"{}\" is missing from the MISO fuel mapping.".format(fuel['CATEGORY']))
            k = 'unknown'
        v = float(fuel['ACT'])
        production[k] = production.get(k, 0.0) + v

    #23-Jan-2018 - Interval 11:45 EST
    timestamp = json_data['RefId']
    split_time = timestamp.split(" ")
    [v for i, v in enumerate(oldlist) if i not in removeset]
    #del split_time[]

    # TODO: join 2 list items then parse, %b month abrev, day zero padded?, %Z for timezone,
    return split_time


def fetch_production(country_code = 'US-MISO'):
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

    json_data = get_json_data(session = None)
    processed_data = data_processer(json_data)

    production = {
      'countryCode': country_code,
      'datetime': None,
      'production': None,
      'storage': {'hydro': None},# TODO: check this
      'source': 'misoenergy.org'
    }

    return processed_data


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
