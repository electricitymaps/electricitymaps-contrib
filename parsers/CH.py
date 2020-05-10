#!/usr/bin/env python3

import arrow
import datetime
import requests
import json
import re

# mapping of the arrow direction to the physical world flow
INTERCO = {
  "CH->FR": {
    "export": "left",
    "import": "right"
  },
  "CH->DE": {
    "export": "top",
    "import": "down"
  },
  "AT->CH": {
    "export": "left",
    "import": "right"
  },
  "CH->IT-NO": {
    "export": "down",
    "import": "top"
  }
}

def get_date_from_payload(p):
  metadatas = p.get('data').get('table')
  ts = list(filter(lambda metadata: metadata['id'] == 'timestamp', metadatas))
  assert(ts[0] is not None)
  
  # ts[0]['label'] is expected to contain something like "Date / time of the values 10.05.2020 14:39:20"
  return arrow.get(ts[0]['label'], 'DD.MM.YYYY HH:mm:ss')

def fetch_exchange(zone_key1='CH', zone_key2='FR', session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This datasource is instantaneous and thus we can\'t go back in time')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))
    if sortedZoneKeys not in INTERCO:
        raise NotImplementedError('This exchange pair is not implemented')

    r = session or requests.session()
    url = 'https://www.swissgrid.ch/bin/services/apicache?path=/content/swissgrid/en/home/operation/grid-data/current-data/jcr:content/parsys/livedatawidget_copy'
    response = r.get(url)
    payload = json.loads(response.content)
    netFlow = None
    
    # loop over all of the interconnexion we got from the widget API
    for i in payload['data']['marker']:
      if i['id'].upper() == 'IT': # hackish key mapping
        i['id'] = 'IT-NO'
      # i[id] == country code with whom switzerland is connected to
      if i['id'].upper() in [zone_key1, zone_key2]:
        assert(i['type'] == 'locationArrow')
        # i['direction'] represents the direction of an arrow on the map
        # here we check that the direction of the arrow makes sense with the interconnection we are considering
        if i['direction'] not in [
            INTERCO[sortedZoneKeys]['import'],
            INTERCO[sortedZoneKeys]['export']
            ]:
          raise(f"An energy flow to {i[id]} in the {i['direction']} direction has been reported by the API but it's not supposed to happen")
        
        # i['text2'] is of the format "62 MW"
        power = int(''.join(filter(str.isdigit, i['text2'])))
        
        # Register the netFlow value in MW. Export = positive value
        if i['direction'] == INTERCO[sortedZoneKeys]['export']:
          netFlow = power
        else: # Imports = Negative value
          netFlow = power*-1
          
    return {
        'datetime': get_date_from_payload(payload).datetime,
        'sortedZoneKeys': sortedZoneKeys,
        'netFlow': netFlow,
        'source': 'https://www.swissgrid.ch/en/home/operation/grid-data/current-data.html'
    }


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_exchange(CH->DE) ->')
    print(fetch_exchange('CH', 'DE'))
    print('fetch_exchange(CH->FR) ->')
    print(fetch_exchange('CH', 'FR'))
    print('fetch_exchange(CH->IT-NO) ->')
    print(fetch_exchange('CH', 'IT-NO'))
    print('fetch_exchange(CH->AT) ->')
    print(fetch_exchange('CH', 'AT'))

