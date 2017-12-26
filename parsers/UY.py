#!/usr/bin/python3

import arrow
import dateutil
import re
import requests

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup

tz = 'America/Montevideo'

MAP_GENERATION = {
  'Hidráulica': 'hydro',
  'Eólica': 'wind',
  'Fotovoltaica': 'solar',
  'Biomasa': 'biomass',
  'Térmica': 'unknown'
}
INV_MAP_GENERATION = dict([(v, k) for (k, v) in MAP_GENERATION.items()])

def parse_page(session):
    r = session or requests.session()
    url = 'http://www.ute.com.uy/SgePublico/ConsPotenciaGeneracionArbolXFuente.aspx'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    datefield = soup.find('span', attrs={'id': 'ctl00_ContentPlaceHolder1_lblUltFecScada'})
    datestr = re.findall('\d\d/\d\d/\d\d\d\d \d+:\d\d', str(datefield.contents[0]))[0]
    date = arrow.get(datestr, 'DD/MM/YYYY h:mm').replace(tzinfo=dateutil.tz.gettz(tz))

    table = soup.find('table', attrs={'id': 'ctl00_ContentPlaceHolder1_gridPotenciasNivel1'})

    obj = {
        'datetime': date.datetime
    }

    for tr in table.find_all('tr'):
        tds = tr.find_all('td')
        if not len(tds): continue

        key = tds[0].find_all('b')
        # Go back one level up if the b tag is not there
        if not len(key): key = tds[0].find_all('font')
        k = key[0].contents[0]

        value = tds[1].find_all('b')
        # Go back one level up if the b tag is not there
        if not len(value): value = tds[1].find_all('font')
        v_str = value[0].contents[0]
        if v_str.find(',') > -1 and v_str.find('.') > -1:
            # there can be values like "1.012,5"
            v_str = v_str.replace('.', '')
            v_str = v_str.replace(',', '.')
        else:
            # just replace decimal separator, like "125,2"
            v_str = v_str.replace(',', '.')
        v = float(v_str)

        # solar reports -0.1 at night, make it at least 0
        v = max(v, 0)

        obj[k] = v

    # Note that the Salto Grande is counted as hydro, whereas it really is a hydro *import*
    # However, because it is coming directly from the hydro dam, we can count it as local production
    # and not as an import. This should be verified though.
    # If this assumption is not correct, then the following line should be uncommented.
    # obj['Hidráulica'] -= max(0, obj['Interconexión Salto Grande'])

    return obj

def fetch_production(country_code='UY', session=None):
    obj = parse_page(session)

    data = {
        'countryCode': country_code,
        'datetime': obj['datetime'],
        'production': dict([(k, obj[INV_MAP_GENERATION[k]]) for k in INV_MAP_GENERATION.keys()]),
        'source': 'ute.com.uy'
    }

    return data

def fetch_exchange(country_code1='UY', country_code2='BR-S', session=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if set([country_code1, country_code2]) != set(['UY', 'BR']):
        return None

    obj = parse_page(session)
    netFlow = obj['Interconexión con Brasil'] # this represents BR->UY (imports)
    if country_code1 != 'BR': netFlow *= -1

    data = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'datetime': obj['datetime'],
        'netFlow': netFlow,
        'source': 'ute.com.uy'
    }

    return data


if __name__ == '__main__':
    print(fetch_production())
    print(fetch_exchange('UY', 'BR'))
