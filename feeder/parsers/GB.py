import arrow
import requests
import xml.etree.ElementTree as ET

COUNTRY_CODE = 'GB'

def fetch_GB():
    url = 'http://www.bmreports.com/bsp/additional/soapfunctions.php?element=generationbyfueltypetable'

    response = requests.get(url)
    root = ET.fromstring(response.content)
    data = root[0]

    parsed = {}
    for item in data:
        parsed[item.get('TYPE')] = float(item.get('VAL'))

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(data.get('AT')).datetime # Time given in UTC
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
    obj['exchange'] = {
        'FR': parsed['INTFR'],
        'IE': parsed['INTIRL'],
        'NL': parsed['INTNED']
    }
    total_production = 0
    for value in obj['production'].values(): total_production += value
    obj['co2'] = (
        parsed['CCGT']/total_production * 360 +
        parsed['OCGT']/total_production * 480 +
        parsed['COAL']/total_production * 910 +
        parsed['OTHER']/total_production * 300 +
        parsed['OIL']/total_production * 610 +
        parsed['INTFR']/total_production * 90 +
        parsed['INTIRL']/total_production * 450 +
        parsed['INTNED']/total_production * 550 +
        parsed['INTEW']/total_production * 450)/0.93

    return obj

if __name__ == '__main__':
    fetch_GB()
