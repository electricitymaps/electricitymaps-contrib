# -*- coding: utf-8 -*-

import arrow
import dateutil
import numpy as np
import requests

COUNTRY_CODE = 'AT'
TIME_ZONE = 'Europe/Vienna'

def fetch_AT():

    now = arrow.now(TIME_ZONE)

    data = {
        'countryCode': COUNTRY_CODE,
        'production': {
            'hydro': 0, 'biomass': 0, 'unknown': 0
        },
        'exchange': {}
    }

    # Fetch production
    url = 'https://www.apg.at/transparency/WebMethods/ChartsEtc.aspx/GetChartData'
    payload = {"PID":"AGPT","DateString":"%s000000" % now.format('YYYYMMDD'),"Resolution":"15M","Language":"en","AdditionalFilter":"B19|B16|B01|B04|B05|B06|B09|B10|B11|B12|B15|B17|B20"}
    obj = requests.post(url, json=payload).json()['d']['ResponseData'][1]
    times = map(lambda d: arrow.get(d['DateLocalString'] + ' ' + d['TimeLocalFromString'], "MM/DD/YYYY HH:mm").replace(tzinfo=dateutil.tz.gettz(TIME_ZONE)).replace(minutes=+15),
        obj['Times'])
    # Fetch values of first item and determine end time
    values = np.array(obj['DataStreams'][0]['ValueStrings'])
    i = np.where(values != '')[0][-1]
    data['datetime'] = times[i].datetime
    for item in obj['DataStreams']:
        name = item['YAxisTitle']
        values = np.array(item['ValueStrings'])
        value = float(values[i].replace(',', ''))
        if name == 'Wind': data['production']['wind'] = max(0, value)
        elif name == 'Solar': data['production']['solar'] = max(0, value)
        elif name == 'Biomass': data['production']['biomass'] += max(0, value)
        elif name == 'Gas': data['production']['gas'] = max(0, value)
        elif name == 'Coal': data['production']['coal'] = max(0, value)
        elif name == 'Oil': data['production']['oil'] = max(0, value)
        elif name == 'Geothermal': data['production']['unknown'] += max(0, value)
        elif name == 'Hydro Pumped Storage': data['production']['hydro'] += max(0, value)
        elif name == 'Hydro Run-of-river and poundage': data['production']['hydro'] += max(0, value)
        elif name == 'Hydro Water Reservoir': data['production']['hydro'] += max(0, value)
        elif name == 'Other renewable': data['production']['unknown'] = max(0, value)
        elif name == 'Waste': data['production']['biomass'] += max(0, value)
        elif name == 'Other': data['production']['unknown'] += max(0, value)

    # Get exchanges
    url = 'https://www.apg.at/transparency/WebMethods/ChartsEtc.aspx/GetMapData'
    payload = {"PID":"CBPF","DateString":"%s000000" % now.format('YYYYMMDD'),"Resolution":"15M","Language":"en","AdditionalFilter": None}
    obj = requests.post(url, json=payload).json()['d']['ResponseData']
    times = map(lambda d: arrow.get(d['DateLocalString'] + ' ' + d['TimeLocalFromString'], "MM/DD/YYYY HH:mm").replace(tzinfo=dateutil.tz.gettz(TIME_ZONE)).replace(minutes=+15),
        obj['Times'])
    i = np.where(np.array(times) <= data['datetime'])[0][-1]
    for item in obj['DataStreams']:
        name = item['YAxisTitle']
        values = np.array(item['ValueStrings'])
        value = float(values[i].replace(' MW', '').replace(',', ''))
        if name == 'CZ>AT': data['exchange']['CZ'] = value
        elif name == 'HU>AT': data['exchange']['HU'] = value
        elif name == 'SI>AT': data['exchange']['SI'] = value
        elif name == 'IT>AT': data['exchange']['IT'] = value
        elif name == 'CH>AT': data['exchange']['CH'] = value
        elif name == 'DE>AT': data['exchange']['DE'] = value

    return data

if __name__ == '__main__':
    print fetch_AT()
