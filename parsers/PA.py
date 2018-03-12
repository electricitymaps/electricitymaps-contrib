#!/usr/bin/env python3
# coding=utf-8

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# The BeautifulSoup library is used to parse HTML
from bs4 import BeautifulSoup


def fetch_production(zone_key='PA', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

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
    
    r = session or requests.session()
    url = 'http://sitr.cnd.com.pa/m/pub/gen.html'
    response = r.get(url)
    response.encoding = 'utf-8'
    html_doc = response.text
    soup = BeautifulSoup(html_doc, 'html.parser')
    productions = soup.find('table', {'class': 'sitr-pie-layout'}).find_all('span')
    map_generation = {
      'Hídrica': 'hydro',
      'Eólica': 'wind',
      'Solar': 'solar',
      'Biogas': 'gas',
      'Térmica': 'unknown'
    }
    data = {
        'zoneKey': 'PA',
        'production': {},
        'storage': {},
        'source': 'https://www.cnd.com.pa/',
    }
    for prod in productions:
        prod_data = prod.string.split(' ')
        production_mean = map_generation[prod_data[0]]
        production_value = float(prod_data[1])
        data['production'][production_mean] = production_value

    # Parse the datetime and return a python datetime object
    spanish_date = soup.find('div', {'class': 'sitr-update'}).find('span').string
    date = arrow.get(spanish_date, 'DD-MMMM-YYYY H:mm:ss', locale="es", tzinfo="America/Panama")
    data['datetime'] = date.datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
