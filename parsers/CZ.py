import arrow
import datetime
import requests
from xml.etree import ElementTree

'''
API Docs: https://www.ceps.cz/en/web-services
Generation Data Visualization: https://www.ceps.cz/en/all-data#Generation
'''

GENERATION_CODES = {
    ''' Mapping of codes defined by CepsData API to electrictymap-contrib labels'''
    'TPP': 'geothermal',
    'CCGT': 'gas',
    'NPP': 'nuclear',
    'HPP': 'hydro',
    'AltPP': 'unknown',
    'PvPP': 'solar',
    'WPP': 'wind',
}

STORAGE_CODES = {
    ''' Mapping of codes defined by CepsData API to electrictymap-contrib labels'''
    'PsPP': 'hydro',
}

CEPS_URL = 'https://www.ceps.cz/_layouts/CepsData.asmx'

HEADERS = {
        'Host': 'www.ceps.cz',
        'Content-Type': 'application/soap+xml; charset=utf-8',
}

SOAP_TEMPLATE = '''<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:xsd="http://www.w3.org/2001/XMLSchema"
xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <Generation xmlns="http://www.ceps.cz/CepsData/">
      <dateFrom>{}</dateFrom>
      <dateTo>{}</dateTo>
      <agregation>QH</agregation>
      <function>AVG</function>
      <version>RT</version>
      <para1>{}</para1>
    </Generation>
  </soap12:Body>
</soap12:Envelope>'''


def fetch_production(zone_key='CZ', session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)  -- request session passed in order to re-use an existing session

    Return:
    An array of dictionary in the form:
    [{
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }]
    """
    if not target_datetime:
        target_datetime = arrow.utcnow()
    url_date = arrow.get(target_datetime).to(
            "Europe/Berlin")
    formatted_date = '{}'.format(url_date)
    unformatted_data = get_data(formatted_date)
    formatted_data = {
        'zoneKey': zone_key,
        'datetime': formatted_date,
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': 0.0,
        },
        'source': 'www.ceps.cz'
    }
    for tag in unformatted_data:
        code = unformatted_data[tag]['name']
        value = unformatted_data[tag]['value']
        production_label = GENERATION_CODES.get(code)
        if production_label:
            formatted_data['production'][production_label] = value
        else:
            storage_label = STORAGE_CODES.get(code)
            if storage_label:
                formatted_data['storage'][storage_label] = value
            elif logger:
                logger.warning('Uncategorized label for code %s', code)
    return [formatted_data]


def get_data(target_datetime):
    """ Get generation data using ceps api """

    formatted_soap = SOAP_TEMPLATE.format(
                                    target_datetime, target_datetime, 'all')
    response = requests.post(CEPS_URL, data=formatted_soap, headers=HEADERS)
    dom = ElementTree.fromstring(response.content)
    series_result = dom.findall(
        '*//{http://www.ceps.cz/CepsData/StructuredData/1.0}serie')
    data = {}
    for series_child in series_result:
        data[series_child.get('id')] = {'name' :
                                    series_child.get('name').split(' ')[0]}
    data_result = dom.findall(
        '*//{http://www.ceps.cz/CepsData/StructuredData/1.0}data')
    for data_child in data_result:
        for sub_data_child in list(data_child):
            for key in sub_data_child.keys():
                if key in data:
                    data[key]['value']=float(sub_data_child.get(key))
    return data


def main():

    print(fetch_production(target_datetime=datetime.datetime(2019, 10, 1)))


if __name__ == '__main__':
    main()
