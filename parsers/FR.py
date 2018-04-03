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


def fetch_production(zone_key='FR', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    if target_datetime:
        now = arrow.get(target_datetime, 'Europe/Paris')
    else:
        now = arrow.now(tz='Europe/Paris')

    r = session or requests.session()
    formatted_from = now.shift(days=-1).format('DD/MM/YYYY')
    formatted_to = now.format('DD/MM/YYYY')
    url = 'http://www.rte-france.com/getEco2MixXml.php?type=mix&dateDeb={}&' \
          'dateFin={}&mode=NORM'.format(formatted_from, formatted_to)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    datas = {}
    mixtr = obj[7]

    for mixtr in obj:
        if mixtr.tag != 'mixtr':
            continue

        start_date = arrow.get(arrow.get(mixtr.attrib['date']).datetime, 'Europe/Paris')

        # Iterate over mix
        for item in mixtr:
            key = item.get('v')
            granularite = item.get('granularite')
            value = None
            # Iterate over time
            for value in item:
                period = int(value.attrib['periode'])
                datetime = start_date.replace(minutes=+(period * 15.0)).datetime
                if not datetime in datas:
                    datas[datetime] = {
                        'zoneKey': zone_key,
                        'datetime': datetime,
                        'production': {},
                        'storage': {},
                        'source': 'rte-france.com',
                    }
                data = datas[datetime]

                if key == 'Hydraulique':
                    # Hydro is a special case!
                    if granularite == 'Global':
                        continue
                    elif granularite in ['FEE', 'LAC']:
                        if not MAP_GENERATION[key] in data['production']:
                            data['production'][MAP_GENERATION[key]] = 0
                        # Run of the river or conventional
                        data['production'][MAP_GENERATION[key]] += float(
                            value.text)
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

    return list(datas.values())


def fetch_price(zone_key, session=None, target_datetime=None,
                logger=logging.getLogger(__name__)):
    if target_datetime:
        now = arrow.get(target_datetime, tz='Europe/Paris')
    else:
        now = arrow.now(tz='Europe/Paris')

    r = session or requests.session()
    formatted_from = now.shift(days=-1).format('DD/MM/YYYY')
    formatted_to = now.format('DD/MM/YYYY')

    url = 'http://www.rte-france.com/getEco2MixXml.php?type=donneesMarche&da' \
          'teDeb={}&dateFin={}&mode=NORM'.format(formatted_from, formatted_to)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    datas = {}

    for donnesMarche in obj:
        if donnesMarche.tag != 'donneesMarche':
            continue

        start_date = arrow.get(arrow.get(donnesMarche.attrib['date']).datetime, 'Europe/Paris')

        for item in donnesMarche:
            if item.get('granularite') != 'Global':
                continue
            country_c = item.get('perimetre')
            if zone_key != country_c:
                continue
            value = None
            for value in item:
                if value.text == 'ND':
                    continue
                period = int(value.attrib['periode'])
                datetime = start_date.replace(hours=+period).datetime
                if not datetime in datas:
                    datas[datetime] = {
                        'zoneKey': zone_key,
                        'currency': 'EUR',
                        'datetime': datetime,
                        'source': 'rte-france.com',
                    }
                data = datas[datetime]
                data['price'] = float(value.text)

    return list(datas.values())


if __name__ == '__main__':
    print(fetch_production())
