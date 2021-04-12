"""Parser for all of India"""

import logging

import arrow
import requests
from bs4 import BeautifulSoup

GENERATION_MAPPING = {'THERMAL GENERATION': 'coal',
                      'GAS GENERATION': 'gas',
                      'HYDRO GENERATION': 'hydro',
                      'NUCLEAR GENERATION': 'nuclear',
                      'RENEWABLE GENERATION': 'unknown'}

GENERATION_URL = 'http://meritindia.in/Dashboard/BindAllIndiaMap'


def get_data(session):
    """
    Requests html then extracts generation data.
    Returns a dictionary.
    """

    s = session or requests.Session()
    req = s.get(GENERATION_URL)
    soup = BeautifulSoup(req.text, 'lxml')
    tables = soup.findAll('table')

    gen_info = tables[-1]
    rows = gen_info.findAll('td')

    generation = {}
    for row in rows:
        gen_title = row.find('div', {"class": "gen_title_sec"})
        gen_val = row.find('div', {"class": "gen_value_sec"})
        val = gen_val.find('span', {"class": "counter"})
        generation[gen_title.text] = val.text.strip()

    return generation


def fetch_production(zone_key = 'IN', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given zone
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple zones
    session (optional) -- request session passed in order to re-use an existing session
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

    if target_datetime is not None:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    raw_data = get_data(session)
    processed_data = {k: float(v.replace(',', '')) for k,v in raw_data.items()}
    processed_data.pop('DEMANDMET', None)

    for k in processed_data:
        if k not in GENERATION_MAPPING.keys():
            processed_data.pop(k)
            logger.warning('Key \'{}\' in IN is not mapped to type.'.format(k), extra={'key': 'IN'})

    mapped_production = {GENERATION_MAPPING[k]: v for k,v in processed_data.items()}

    data = {
      'zoneKey': zone_key,
      'datetime': arrow.now('Asia/Kolkata').datetime,
      'production': mapped_production,
      'storage': {},
      'source': 'meritindia.in'
    }

    return data

if __name__ == '__main__':
    print('fetch_production() -> ')
    print(fetch_production())
