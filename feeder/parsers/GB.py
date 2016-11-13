import arrow
import requests
import xml.etree.ElementTree as ET

def fetch(session=None):
    url = 'http://www.bmreports.com/bsp/additional/soapfunctions.php?element=generationbyfueltypetable'

    response = (session or requests).get(url)
    root = ET.fromstring(response.content)
    data = root[0]

    return data

def fetch_production(country_code='GB', session=None):
    data = fetch(session)
    parsed = {}
    for item in data:
        parsed[item.get('TYPE')] = float(item.get('VAL'))

    obj = {
        'countryCode': country_code,
        'datetime': arrow.get(data.get('AT')).datetime, # Time given in UTC
        'source': 'bmreports.com'
    }
    obj['consumption'] = {}
    obj['production'] = {
        'coal': parsed['COAL'],
        'gas': parsed['CCGT'] + parsed['OCGT'],
        'nuclear': parsed['NUCLEAR'],
        'wind': parsed['WIND'],
        'oil': parsed['OIL'],
        'hydro': parsed['PS'] + parsed['NPSHYD'],
        'unknown': parsed['OTHER']
    }

    return obj

def fetch_exchange(country_code1, country_code2, session=None):
    if country_code1 == 'GB': 
        direction = 1
        target = country_code2
    elif country_code2 == 'GB': 
        direction = -1
        target = country_code1
    else: return None
    data = fetch(session)
    parsed = {}
    for item in data:
        parsed[item.get('TYPE')] = float(item.get('VAL'))
    obj = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'datetime': arrow.get(data.get('AT')).datetime, # Time given in UTC
        'source': 'bmreports.com'
    }
    if target == 'FR':
        obj['netFlow'] = direction * parsed['INTFR']
    elif target == 'IE':
        obj['netFlow'] = direction * parsed['INTIRL']
    elif target == 'NL':
        obj['netFlow'] = direction * parsed['INTNED']
    else: raise Exception('Unhandled case')
    return obj

if __name__ == '__main__':
    fetch_production()
