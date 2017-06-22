#!/usr/bin/python
# -*- coding: utf-8 -*-

import arrow
import dateutil
import requests

MAP_GENERATION = {
  'aes': 'nuclear',
  'tec': 'other', # fossil 
  'tes': 'coal',
  'chpp': 'gas',
  'hpp': 'hydro',
  'vde': 'wind',
  'gesgaes' : 'gesgaes', # hydro pumped storage
  'consumptiongaespump' :'consumptiongaespump' #hydro run of river and poundage
}
MAP_OTHER   = {
  'consumption' : 'consumption',
  'hour' : 'hour'
}

tz = 'Europe/Kiev'

def fetch_production(country_code='UA', session=None):
    r = session or requests.session()
    
    today =  arrow.now(tz=tz).format('DD.MM.YYYY')
    url = 'https://ua.energy/wp-admin/admin-ajax.php'
    postdata = {
      'action': 'get_data_oes',
      'report_date': arrow.now(tz=tz).format('DD.MM.YYYY'),
      'type': 'day',
      'rnd': 0.2046847583117225
    }
    response = r.post(url, postdata)
    obj = response.json()
    allofit = []
    for serie in obj:
        data = []
        data.append({
            'countryCode': country_code,
            'production': {},
            'source': 'ua.energy'            
        })
        for key in serie:
            key = key.encode('utf-8')
            if key in MAP_GENERATION:
                if key in ('gesgaes', 'consumptiongaespump'):
                   data[0]['production']['hydro'] = serie['gesgaes'] + serie['consumptiongaespump']
                else:
                   data[0]['production'][MAP_GENERATION[key]] = serie[key]
            if key in MAP_OTHER:
                this = str(today) + ' ' + str(serie['hour'])
                dumpdate = arrow.get(this, 'DD.MM.YYYY HH:mm').replace(tzinfo=dateutil.tz.gettz(tz))
                data[0]['datetime'] = dumpdate.datetime
        allofit.append(data)

    return allofit  
     
     
if __name__ == '__main__':
    print fetch_production()
