#!/usr/bin/env python3

import logging
import requests
import lxml
from bs4 import BeautifulSoup
import re
import json
import arrow

TZ = 'Pacific/Tahiti'

def fetch_production(
    zone_key='PF',
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
):
    """Requests the last known production mix (in MW) of a given country
    Arguments:
    ----------
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not
      provided, we should default it to now. If past data is not available,
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
    logger: an instance of a `logging.Logger` that will be passed by the
      backend. Information logged will be publicly available so that correct
      execution of the logger can be checked. All Exceptions will automatically
      be logged, so when something's wrong, simply raise an Exception (with an
      explicit text). Use `logger.warning` or `logger.info` for information
      that can useful to check if the parser is working correctly. A default
      logger is used so that logger output can be seen when coding / debugging.
    Returns:
    --------
    If no data can be fetched, any falsy value (None, [], False) will be
      ignored by the backend. If there is no data because the source may have
      changed or is not available, raise an Exception.
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
    r = session or requests.Session()
    if target_datetime is None:
        url = "https://www.edt.pf/transition-energetique-innovation"  
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    res = r.get(url)
    assert res.status_code == 200, 'Exception when fetching production for ' \
                                   '{}: error when calling url={}'.format(zone_key, url)
    
    soup = BeautifulSoup(res.text, 'lxml')
    block = soup.find(id="id1____detailMesurePortlet__WAR__EDTAEL2018__Script").prettify()
    block = block.replace('\n','')
    block = re.search(r'\{"cols.*\}\]\}\]\}', block)

    data_table = block.group(0)
    data_table = re.sub('Thermique', 'oil', data_table)
    data_table = re.sub('Hydro électricité', 'hydro', data_table)
    data_table = re.sub('Solaire', 'solar', data_table)
            
    data_dict = json.loads(data_table)

    data = {
        'zoneKey': zone_key,
        'datetime': arrow.utcnow().floor('minute').datetime,
        'production': {
        'biomass': 0.0,
        'coal': 0.0,
        'gas': 0.0,
        'hydro': None,
        'nuclear': 0.0,
        'oil': None,
        'solar': None,
        'wind': None,
        'geothermal': 0.0,
        'unknown': None
        },
        'storage': {},
        'source': 'edt.pf'
    }

    # Parse the dict 'data_dict' containing the production mix (the values are in kW)
    for line in data_dict['rows']:
        resource = line['c'][0].get('v')
        production_value = line['c'][1].get('v')
        production_value_mw = production_value/1000
        data['production'][resource] = production_value_mw
        
    return data

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    print('fetch_production() ->')
    print(fetch_production())
