#!/usr/bin/python
# -*- coding: utf-8 -*-

import arrow
import requests
import xml.etree.ElementTree as ET

MAP_GENERATION = {
    'Vand': 'hydro',
    'Olie': 'oil',
    'Diesel': 'oil',
    'Vind': 'wind'
}
def getDataKey(tag):
    return MAP_GENERATION.get(tag, None)

def fetch_production(country_code='FO', session=None):
    r = session or requests.session()
    url = 'https://w3.sev.fo/hagtol/xml/xkiefjSDKFjeijgjdkjf3847tgfjlkfdgnlsnfvm.xml'
    response = r.get(url)
    obj = ET.fromstring(response.content)[0]
    
    data = {
        'countryCode': country_code,
        'capacity': {},
        'production': {
            'biomass': 0,
            'coal': 0,
            'gas': 0,
            'geothermal': 0,
            'nuclear': 0,
            'solar': 0
        },
        'storage': {},
        'source': 'sev.fo',
    }
    for item in obj:
        if item.tag == 'tiden':
            data['datetime'] = arrow.get(
                arrow.get(item.text).datetime, 'Atlantic/Faroe').datetime
        elif 'Sum' in item.tag:
            continue
        elif 'Test' in item.tag:
            continue
        elif 'VnVand' in item.tag:
            # This is the sum of hydro (Mýrarnar + Fossá + Heygar)
            continue
        elif item.tag.endswith('Sev_E'):
            # E stands for Energy
            tag = item.tag.replace('Sev_E', '')
            key = getDataKey(tag)
            if not key: continue
            # Power (MW)
            value = float(item.text.replace(',', '.'))
            data['production'][key] = data['production'].get(key, 0) + value
        else:
            # print 'Unhandled key %s' % item.tag
            pass

    return data

print fetch_production()
