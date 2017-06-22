#!/usr/bin/python
# -*- coding: utf-8 -*-

import arrow
import dateutil
import requests

MAP_GENERATION = {
  'aes': 'nuclear',
  'tec': 'biomass',
  'tes': 'coal',
  'chpp': 'gas',
  'hpp': 'hydro',
  'vde': 'wind',
  'gesgaes' : 'gesgaes',
  'consumption' : 'consumption',
  'hour' : 'hour',
  'consumptiongaespump' :'consumptiongaespump'
}

tz = 'Europe/Kiev'

def fetch_production(country_code='UA', session=None):
    r = session or requests.session()
    today =  arrow.now(tz=tz).format('DD.MM.YYYY')
    print today
    url = 'https://ua.energy/wp-admin/admin-ajax.php'
    postdata = {
      'action': 'get_data_oes',
      'report_date': arrow.now(tz=tz).format('DD.MM.YYYY'),
      'type': 'day',
      'rnd': 0.2046847583117225
    }
    response = r.post(url, postdata)
    obj = response.json()
    print obj
    for serie in obj:
        for key in serie:
           key = key.encode('utf-8')
           print today, key
           if not key in MAP_GENERATION:
             raise Exception('Unknown production type %s' %key)
           print key , serie[key];
    


if __name__ == '__main__':
    print fetch_production()
