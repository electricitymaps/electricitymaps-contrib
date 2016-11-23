import arrow
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
}

def fetch_production(country_code='FR', session=None):
    r = session or requests.session()
    formatted_date = arrow.now(tz='Europe/Paris').format('DD/MM/YYYY')
    url = 'http://www.rte-france.com/getEco2MixXml.php?type=mix&&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_date, formatted_date)
    response = r.get(url)
    obj = ET.fromstring(response.content)
    mixtr = obj[7]
    data = {
        'countryCode': country_code,
        'production': {},
        'consumption': {},
        'source': 'rte-france.com',
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

    data['datetime'] = arrow.get(arrow.get(obj[1].text).datetime, 
        'Europe/Paris').replace(minutes=+(int(value.attrib['periode']) * 15.0)).datetime

    # Fetch imports
    # url = 'http://www.rte-france.com/getEco2MixXml.php?type=echcom&&dateDeb={}&dateFin={}&mode=NORM'.format(formatted_date, formatted_date)
    # response = r.get(url)
    # obj = ET.fromstring(response.content)
    # parsed = {}
    # for item in obj[7].getchildren():
    #     value = None
    #     for value in item: pass
    #     parsed[item.get('v')] = float(value.text)

    # data['exchange'] = {
    #     'CH': parsed['CH'],
    #     'GB': parsed['GB'],
    #     'ES': parsed['ES'],
    #     'IT': parsed['IT'],
    #     'DE': parsed['DB'] # Germany + Belgium redirected to Germany
    # }

    return data

if __name__ == '__main__':
    print fetch_production()
