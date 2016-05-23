import arrow
import requests
import xml.etree.ElementTree as ET

COUNTRY_CODE = 'FR'
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
}

def fetch_FR():
    r = requests.session()
    formatted_date = arrow.now(tz='Europe/Paris').format('DD/MM/YYYY')
    url = 'http://www.rte-france.com/getEco2MixXml.php?type=mix&&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_date, formatted_date)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    mixtr = obj[7]
    data = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(arrow.get(obj[0].text).datetime, 
            'Europe/Paris').datetime,
        'production': {},
        'consumption': {}
    }
    for item in mixtr.getchildren():
        if item.get('granularite') != 'Global': continue
        key = item.get('v')
        value = None
        for value in item.getchildren(): pass
        if key in MAP_GENERATION:
            data['production'][MAP_GENERATION[key]] = float(value.text)
        elif key in MAP_STORAGE:
            data['consumption'][MAP_STORAGE[key]] = float(value.text)

    # Fetch co2
    url ='http://www.rte-france.com/getEco2MixXml.php?type=co2&&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_date, formatted_date)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    value = None
    for value in obj[7][0].getchildren(): pass
    data['co2'] = float(value.text)

    return data
