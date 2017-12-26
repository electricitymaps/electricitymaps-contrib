#!/usr/bin/env python3

# Parser for the Chile-SING region.
# There are plans to unify the Chilean grid.
# https://www.engerati.com/article/chile%E2%80%99s-grid-be-unified-new-transmission-highway

from __future__ import print_function
from bs4 import BeautifulSoup
from collections import defaultdict
import datetime
import json
from pytz import timezone
import re
import requests

url = 'https://sger.coordinadorelectrico.cl/Charts/AmChartCurvaCompuesta?showinfo=True'

plant_map = {
             u"Generacion_Neta": "unknown",
             u"Real Andes Solar": "solar",
             u"Real Bolero": "solar",
             u"Real Cerro Dominador PV": "solar",
             u"Real Finis Terrae": "solar",
             u"Real La Huayca 2": "solar",
             u"Real Mar\xeda Elena FV": "solar",
             u"Real PAS2": "solar",
             u"Real PAS3": "solar",
             u"Real Pampa Camarones": "solar",
             u"Real Parque Eolico Sierra Gorda Este": "wind",
             u"Real Puerto Seco Solar": "solar",
             u"Real Solar El Aguila 1": "solar",
             u"Real Solar Jama": "solar",
             u"Real Solar Jama 2": "solar",
             u"Real Uribe": "solar",
             u"Real Valle de los Vientos": "wind",
             u"date": "datetime"
             }


def get_data(session=None):
    """
    Makes a GET request to the data url.  Parses the returned page to find the
    data which is contained in a javascript variable.
    Returns a list of dictionaries.
    """

    s = session or requests.Session()
    datareq = s.get(url)
    soup = BeautifulSoup(datareq.text, 'html.parser')
    chartdata = soup.find('script', type="text/javascript").text

    # regex that finds js var called chartData, list can be variable length.
    pattern = r'chartData = \[(.*)\]'
    match = re.search(pattern, chartdata)
    rawdata = match.group(0)

    # Cut down to just the list.
    start = rawdata.index('[')
    sliced = rawdata[start:]
    loaded_data = json.loads(sliced)

    return loaded_data


def convert_time_str(ts):
    """Takes a unicode time string and converts into an aware datetime object."""

    dt_naive = datetime.datetime.strptime(ts, '%Y-%m-%d %H:%M')
    localtz = timezone('Chile/Continental')
    dt_aware = localtz.localize(dt_naive)

    return dt_aware


def data_processer(data):
    """
    Takes raw production data and converts it into a usable form.
    Removes unneeded keys and sums generation types.
    Returns a list.
    """

    clean_data = []
    for datapoint in data:
        bad_keys = (u'Total_ERNC', u'Generacion Total')
        for bad in bad_keys:
            datapoint.pop(bad, None)

        for key in datapoint.keys():
            if key not in plant_map.keys():
                print('{} is missing from the CL_SING plant mapping.'.format(key))

        mapped_plants = [(plant_map.get(plant, 'unknown'), val) for plant, val
                         in datapoint.items()]
        datapoint = defaultdict(lambda: 0.0)

        # Sum values for duplicate keys.
        for key, val in mapped_plants:
            try:
                datapoint[key] += val
            except TypeError:
                # datetime key is a string!
                datapoint[key] = val

        datapoint['datetime'] = convert_time_str(datapoint['datetime'])
        clean_data.append(datapoint)

    return clean_data


def fetch_production(country_code='CL-SING', session=None):
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

    gd = get_data(session=None)
    dp = data_processer(gd)
    production_mix_by_hour = []
    for point in dp:
        production_mix = {
          'countryCode': country_code,
          'datetime': point['datetime'],
          'production': {
              'solar': point.get('solar', 0.0),
              'wind': point.get('wind', 0.0),
              'unknown': point.get('unknown', 0.0)
          },
          'source': 'sger.coordinadorelectrico.cl'
        }
        production_mix_by_hour.append(production_mix)

    return production_mix_by_hour


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
