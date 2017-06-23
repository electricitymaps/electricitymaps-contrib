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
  'gesgaes' : 'hydro', #hydro run of river and poundage 
  'consumptiongaespump' : 'consumptiongaespump' # hydro pumped storage
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
    
    dataDict = []    
    for serie in obj:
        dataDict.append({
            'countryCode': country_code,
            'production': {},
            'storage' : {},
            'source': 'ua.energy'
        })
        for key in serie:
            i =  len(dataDict)-1
            key = key.encode('utf-8')
            this = str(today) + ' ' + str(serie['hour'])
            dumpdate = arrow.get(this, 'DD.MM.YYYY HH:mm').replace(tzinfo=dateutil.tz.gettz(tz))
            dataDict[i]['datetime'] = dumpdate.datetime
            
            if key in MAP_GENERATION:
                if key == 'consumptiongaespump':
                   dataDict[i]['storage']['hydro'] = serie['consumptiongaespump']
                else:
                   dataDict[i]['production'][MAP_GENERATION[key]] = serie[key]

    return dataDict  
     
     
if __name__ == '__main__':
    print fetch_production()
