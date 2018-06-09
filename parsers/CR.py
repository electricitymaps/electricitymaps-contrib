#!/usr/bin/env python3
# coding=utf-8

import logging

import arrow
import pandas as pd
import requests
from bs4 import BeautifulSoup

TIMEZONE = 'America/Costa_Rica'
DATE_FORMAT = 'DD/MM/YYYY'
MONTH_FORMAT = 'MM/YYYY'
POWER_PLANTS = {
    u'Aeroenergía': 'wind',
    u'Altamira': 'wind',
    u'Angostura': 'hydro',
    u'Arenal': 'hydro',
    u'Balsa Inferior': 'hydro',
    u'Barranca': 'unknown',
    u'Barro Morado': 'geothermal',
    u'Bijagua': 'hydro',
    u'Birris12': 'hydro',
    u'Birris3': 'hydro',
    u'Boca de Pozo': 'hydro',
    u'CNFL': 'unknown',
    u'Cachí': 'hydro',
    u'Campos Azules': 'wind',
    u'Canalete': 'unknown',
    u'Cariblanco': 'hydro',
    u'Carrillos': 'hydro',
    u'Caño Grande': 'hydro',
    u'Caño Grande III': 'hydro',
    u'Chiripa': 'wind',
    u'Chocosuelas': 'hydro',
    u'Chucás': 'hydro',
    u'Cubujuquí': 'hydro',
    u'Daniel Gutiérrez': 'hydro',
    u'Dengo': 'hydro',
    u'Don Pedro': 'hydro',
    u'Doña Julia': 'hydro',
    u'Echandi': 'hydro',
    u'El Angel': 'hydro',
    u'El Angel Ampliación': 'hydro',
    u'El Embalse': 'hydro',
    u'El General': 'hydro',
    u'El Viejo': 'biomass',
    u'Garabito': 'oil',
    u'Garita': 'hydro',
    u'Guápiles': 'oil',
    u'Hidrozarcas': 'hydro',
    u'La Esperanza (CoopeL)': 'hydro',
    u'La Joya': 'hydro',
    u'Los Negros': 'hydro',
    u'Los Negros II': 'hydro',
    u'Los Santos': 'wind',
    u'MOVASA': 'wind',
    u'Matamoros': 'unknown',
    u'Miravalles I': 'geothermal',
    u'Miravalles II': 'geothermal',
    u'Miravalles III': 'geothermal',
    u'Miravalles V': 'geothermal',
    u'Moín I': 'oil',
    u'Moín II': 'oil',
    u'Moín III': 'oil',
    u'Orosí': 'wind',
    u'Orotina': 'unknown',
    u'Otros': 'unknown',
    u'PE Mogote': 'wind',
    u'PEG': 'wind',
    u'Pailas': 'geothermal',
    u'Parque Solar Juanilama': 'solar',
    u'Parque Solar Miravalles': 'solar',
    u'Peñas Blancas': 'hydro',
    u'Pirrís': 'hydro',
    u'Plantas Eólicas': 'wind',
    u'Platanar': 'hydro',
    u'Pocosol': 'hydro',
    u'Poás I y II': 'hydro',
    u'Reventazón': 'hydro',
    u'Río Lajas': 'hydro',
    u'Río Macho': 'hydro',
    u'San Antonio': 'oil',
    u'San Lorenzo (C)': 'hydro',
    u'Sandillal': 'hydro',
    u'Suerkata': 'hydro',
    u'Taboga': 'biomass',
    u'Tacares': 'hydro',
    u'Tejona': 'wind',
    u'Tilawind': 'wind',
    u'Torito': 'hydro',
    u'Toro I': 'hydro',
    u'Toro II': 'hydro',
    u'Toro III': 'hydro',
    u'Tuis (JASEC)': 'hydro',
    u'Valle Central': 'wind',
    u'Vara Blanca': 'hydro',
    u'Ventanas-Garita': 'hydro',
    u'Vientos de La Perla': 'wind',
    u'Vientos de Miramar': 'wind',
    u'Vientos del Este': 'wind',
    u'Volcán': 'hydro',
}

CHARACTERISTIC_NAME = 'Angostura'


def empty_record(zone_key):
    return {
        'zoneKey': zone_key,
        'capacity': {},
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
        'storage': {},
        'source': 'grupoice.com'
    }


def df_to_data(zone_key, day, df, logger):
    df = df.dropna(axis=1, how='any')
    # Check for empty dataframe
    if df.shape == (1, 1):
        return []
    df = df.drop(['Intercambio Sur', 'Intercambio Norte', 'Total'], errors='ignore')
    df = df.iloc[:, :-1]

    results = []
    unknown_plants = set()
    hour = 0
    for column in df:
        data = empty_record(zone_key)
        data_time = day.replace(hour=hour, minute=0, second=0, microsecond=0).datetime
        for index, value in df[column].items():
            source = POWER_PLANTS.get(index)
            if not source:
                source = 'unknown'
                unknown_plants.add(index)
            data['datetime'] = data_time
            data['production'][source] += max(0.0, value)
        hour += 1
        results.append(data)

    for plant in unknown_plants:
        logger.warning('{} is not mapped to generation type'.format(plant),
                       extra={'key': zone_key})

    return results


def fetch_production(zone_key='CR', session=None,
                     target_datetime=None, logger=logging.getLogger(__name__)):
    # ensure we have an arrow object. if no target_datetime is specified, this defaults to now.
    target_datetime = arrow.get(target_datetime).to(TIMEZONE)

    if target_datetime < arrow.get('2012-07-01'):
        # data availability limit found by manual trial and error
        logger.error('CR API does not provide data before 2012-07-01, '
                     '{} was requested'.format(target_datetime),
                     extra={"key": zone_key})
        return None

    # Do not use existing session as some amount of cache is taking place
    r = requests.session()
    url = 'https://appcenter.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    response = r.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    jsf_view_state = soup.select('#javax.faces.ViewState')[0]['value']

    data = [
        ('formPosdespacho', 'formPosdespacho'),
        ('formPosdespacho:txtFechaInicio_input', target_datetime.format(DATE_FORMAT)),
        ('formPosdespacho:pickFecha', ''),
        ('formPosdespacho:j_idt60_selection', ''),
        ('formPosdespacho:j_idt60_scrollState', '0,1915'),
        ('javax.faces.ViewState', jsf_view_state),
    ]
    response = r.post(url, cookies={}, data=data)

    # tell pandas which table to use by providing CHARACTERISTIC_NAME
    df = pd.read_html(response.text, match=CHARACTERISTIC_NAME, skiprows=1, index_col=0)[0]

    results = df_to_data(zone_key, target_datetime, df, logger)

    return results


def fetch_exchange(zone_key1='CR', zone_key2='NI', session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two regions

    Arguments:
    zone_key1           -- the first country code
    zone_key2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }

    where net flow is from DK into NO
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))

    df = pd.read_csv('http://www.enteoperador.org/newsite/flash/data.csv', index_col=False)

    if sorted_zone_keys == 'CR->NI':
        flow = df['NICR'][0]
    elif sorted_zone_keys == 'CR->PA':
        flow = -1 * df['CRPA'][0]
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    data = {
        'datetime': arrow.now(TIMEZONE).datetime,
        'sortedZoneKeys': sorted_zone_keys,
        'netFlow': flow,
        'source': 'enteoperador.org'
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    from pprint import pprint

    print('fetch_production() ->')
    pprint(fetch_production())

    print('fetch_production(target_datetime=arrow.get("2018-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get('2018-03-13T12:00Z')))

    # this should work
    print('fetch_production(target_datetime=arrow.get("2013-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get('2013-03-13T12:00Z')))

    # this should return None
    print('fetch_production(target_datetime=arrow.get("2007-03-13T12:00Z") ->')
    pprint(fetch_production(target_datetime=arrow.get('2007-03-13T12:00Z')))

    print('fetch_exchange() ->')
    print(fetch_exchange())
