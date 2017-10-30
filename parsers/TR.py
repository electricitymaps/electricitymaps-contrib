import requests
import re
import json
import arrow

SEARCH_DATA = re.compile(r'var gunlukUretimEgrisiData = (?P<data>.*);')
TIMEZONE = 'Europe/Istanbul'
URL = 'https://ytbs.teias.gov.tr/ytbs/frm_login.jsf'
EMPTY_DAY = -1

MAP_GENERATION = {
    'akarsu': 'hydro',
    'barajli': 'hydro',
    'dogalgaz': 'gas',
    'jeotermal': 'geothermal',
    'taskomur': 'coal',
    'asfaltitkomur': 'coal',
    'linyit': 'coal',
    'ithalkomur': 'coal',
    'ruzgar': 'wind',
    'fueloil': 'oil',
    'biyokutle': 'biomass',
    'nafta': 'unknown'
}


def as_float(prod):
    """Convert json values to float and sum all production for a further use"""
    prod['total'] = 0.0
    if isinstance(prod, dict) and 'yuk' not in prod.keys():
        for prod_type, prod_val in prod.items():
            prod[prod_type] = float(prod_val)
            prod['total'] += prod[prod_type]
    return prod


def get_last_data_idx(productions):
    """
    Find index of the last production
    :param productions: list of 24 production dict objects
    :return: (int) index of the newest data or -1 if no data (empty day)
    """
    for i in range(len(productions)):
        if productions[i]['total'] < 1000:
            return i - 1
    return len(productions) - 1  # full day


def fetch_production(country_code='TR', session=None):
    session = None # Explicitely make a new session to avoid caching from their server...
    r = session or requests.session()
    tr_datetime = arrow.now().to('Europe/Istanbul').floor('day')
    data = {
      'countryCode': country_code,
      'production': {},
      'storage': {},
      'source': 'ytbs.teias.gov.tr',
      'datetime': tr_datetime.datetime
    }
    response = r.get(URL, verify=False)
    str_data = re.search(SEARCH_DATA, response.text)
    if str_data:
        productions = json.loads(str_data.group('data'), object_hook=as_float)
        last_data_index = get_last_data_idx(productions)
        if last_data_index != EMPTY_DAY:
            last_prod = productions[last_data_index]
            data['production'] = dict(zip(MAP_GENERATION.values(), [0] * len(MAP_GENERATION)))
            for prod_type, prod_val in last_prod.items():
                if prod_type in MAP_GENERATION.keys():
                    data['production'][MAP_GENERATION[prod_type]] += prod_val
            data['datetime'] = tr_datetime.replace(hour=last_data_index).datetime
    else:
        raise Exception('Extracted data was None')
    return data

if __name__ == '__main__':
    res = fetch_production()
    print res
    print sum(res['production'].values())
