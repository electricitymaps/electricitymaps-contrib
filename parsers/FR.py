#!/usr/bin/env python3

import arrow
import logging
import requests
import xml.etree.ElementTree as ET

MAP_GENERATION = {
    u'Nucl\xe9aire': 'nuclear',
    'Charbon': 'coal',
    'Gaz': 'gas',
    'Fioul': 'oil',
    'Hydraulique': 'hydro',
    'Eolien': 'wind',
    'Solaire': 'solar',
    'Autres': 'biomass'
}
MAP_STORAGE = {
    'Pompage': 'hydro',
    'Hydraulique': 'hydro',
}


def fetch_production(zone_key='FR', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    now = arrow.get(target_datetime, 'Europe/Paris') if target_datetime else arrow.now(tz='Europe/Paris')

    r = session or requests.session()
    formatted_from = now.shift(days=-1).format('DD/MM/YYYY')
    formatted_to = now.format('DD/MM/YYYY')
    url = 'http://www.rte-france.com/getEco2MixXml.php?type=mix&&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_from, formatted_to)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    mixtr = obj[7]
    date = arrow.get(arrow.get(obj[1].text).datetime, 'Europe/Paris')
    datas = []

    # Iterate over mix
    for item in mixtr.getchildren():
        key = item.get('v')
        granularite = item.get('granularite')
        value = None
        # Iterate over time
        for value in item.getchildren():
            # Figure out time index
            i = int(value.attrib['periode'])
            if i >= len(datas):
                datas.append({
                    'zoneKey': zone_key,
                    'datetime': date.replace(minutes=+(i * 15.0)).datetime,
                    'production': {},
                    'storage': {},
                    'source': 'rte-france.com',
                })
            data = datas[i]

            if key == 'Hydraulique':
                # Hydro is a special case!
                if granularite == 'Global':
                    continue
                elif granularite in ['FEE', 'LAC']:
                    if not MAP_GENERATION[key] in data['production']:
                        data['production'][MAP_GENERATION[key]] = 0
                    # Run of the river or conventional
                    data['production'][MAP_GENERATION[key]] += float(value.text)
                elif granularite == 'STT':
                    if not MAP_STORAGE[key] in data['storage']:
                        data['storage'][MAP_STORAGE[key]] = 0
                    # Pumped storage generation
                    data['storage'][MAP_STORAGE[key]] += -1 * float(value.text)
            elif granularite == 'Global':
                if key in MAP_GENERATION:
                    data['production'][MAP_GENERATION[key]] = float(value.text)
                elif key in MAP_STORAGE:
                    if not MAP_STORAGE[key] in data['storage']:
                        data['storage'][MAP_STORAGE[key]] = 0
                    data['storage'][MAP_STORAGE[key]] += -1 * float(value.text)

    return datas


def fetch_price(zone_key, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    now = arrow.get(target_datetime, 'Europe/Paris') if target_datetime else arrow.now(tz='Europe/Paris')

    r = session or requests.session()
    formatted_from = now.shift(days=-1).format('DD/MM/YYYY')
    formatted_to = now.format('DD/MM/YYYY')

    url = 'http://www.rte-france.com/getEco2MixXml.php?type=donneesMarche&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_from, formatted_to)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    mixtr = obj[5]

    prices = []
    datetimes = []

    date_str = mixtr.get('date')
    date = arrow.get(arrow.get(date_str).datetime, 'Europe/Paris')
    for country_item in mixtr.getchildren():
        if country_item.get('granularite') != 'Global':
            continue
        country_c = country_item.get('perimetre')
        if zone_key != country_c:
            continue
        value = None
        for value in country_item.getchildren():
            if value.text == 'ND':
                continue
            datetime = date.replace(hours=+int(value.attrib['periode'])).datetime
            datetimes.append(datetime)
            prices.append(float(value.text))

    data = [{
        'zoneKey': zone_key,
        'currency': 'EUR',
        'datetime': datetimes[i],
        'price': prices[i],
        'source': 'rte-france.com',
    } for i in range(len(prices))]
    return data


if __name__ == '__main__':
    print(fetch_production())
