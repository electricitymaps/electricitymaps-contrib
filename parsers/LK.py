#!/usr/bin/env python3

from arrow import get
from requests import Session

from parsers import countrycode
from parsers.lib import web


def fetch_data(country_code, session=None):
    countrycode.assert_country_code(country_code, 'LK')

    html = web.get_response_soup(country_code, 'http://www.ceb.lk/yesterday-electricity/', session)
    date = get(html.find_all('h4')[1].text.strip().split(':')[-1], 'MMMM D, YYYY')
    head_vals = html.find_all('div', {'class': 'wpb_wrapper'})[3].find_all('div', {'class': 'row'})

    demand = float(head_vals[0].text.strip().split('\n')[1].split(' ')[0])
    storage = float(head_vals[1].text.strip().split('\n')[1].split(' ')[0])

    rows = html.find_all('tr')[1:]

    oil_value = wind_value = hydro_value = coal_value = 0.0

    for row in rows:
        values = row.text.lower().strip().split('\n')
        if 'coal' in values[0]:
            coal_value += float(values[1].split(' ')[0])
        elif 'oil' in values[0]:
            oil_value += float(values[1].split(' ')[0])
        elif 'wind' in values[0]:
            wind_value += float(values[1].split(' ')[0])
        else:
            hydro_value += float(values[1].split(' ')[0])

    value_map = {
        "date": date.datetime,
        "solar": None,
        "oil": float('%.2f' % float(oil_value * 1000)),
        "hydro": float('%.2f' % float(hydro_value * 1000)),
        "thermal": None,
        "wind": float('%.2f' % float(wind_value * 1000)),
        "gas": None,
        "nuclear": None,
        "coal": float('%.2f' % float(coal_value * 1000)),
        "demand": float('%.2f' % demand),
        "storage": float(storage * 1000)
    }

    return value_map


def fetch_production(country_code='LK', session=None):
    """
    Method to get production data of SriLanka
    :param country_code:
    :param session:
    :return:
    """
    value_map = fetch_data(country_code, session)

    data = {
        'countryCode': country_code,
        'datetime': value_map['date'],
        'production': {
            'biomass': None,
            'coal': value_map['coal'],
            'gas': value_map['gas'],
            'hydro': value_map['hydro'],
            'nuclear': value_map['nuclear'],
            'oil': value_map['oil'],
            'solar': value_map['solar'],
            'wind': value_map['wind'],
            'geothermal': None,
            'unknown': None
        },
        'storage': {
            'hydro': value_map['storage']
        },
        'source': 'ceb.lk',
    }

    return data


def fetch_consumption(country_code='LK', session=None):
    """
    Method to get consumption data of SriLanka
    :param country_code:
    :param session:
    :return:
    """
    value_map = fetch_data(country_code, session)

    data = {
        'countryCode': country_code,
        'datetime': value_map['date'],
        'consumption': value_map['demand'],
        'source': 'ceb.lk'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('LK', session))
    print(fetch_consumption('LK', session))
