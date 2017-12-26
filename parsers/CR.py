#!/usr/bin/env python3

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
    u'Los Santos': 'wind',
    u'MOVASA': 'wind',
    u'Matamoros': 'unknown',
    u'Miravalles I': 'geothermal',
    u'Miravalles II': 'geothermal',
    u'Miravalles III': 'geothermal',
    u'Miravalles V': 'geothermal',
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

unmapped = set()


def unknown_plants():
    for plant in unmapped:
        print('{} is not mapped to generation type!'.format(plant))


def empty_record(country_code):
    return {
        'countryCode': country_code,
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


def df_to_data(country_code, day, df):
    df = df.dropna(axis=1, how='any')
    # Check for empty dataframe
    if df.shape == (1, 1):
        return []
    df = df.drop([u'Intercambio Sur', u'Intercambio Norte', u'Total'])
    df = df.iloc[:, :-1]

    data = []
    hours = 0
    for column in df:
        data.append(empty_record(country_code))
        for index, value in df[column].items():
            current = len(data) - 1
            source = POWER_PLANTS.get(index)
            if source is None:
                source = 'unknown'
                unmapped.add(index)
            data[current]['datetime'] = day.replace(hours=hours).datetime
            data[current]['production'][source] += max(0.0, value)
        hours += 1

    return data


def fetch_production(country_code='CR', session=None):
    # Do not use existing session as some amount of cache is taking place
    r = requests.session()
    url = 'https://appcenter.grupoice.com/CenceWeb/CencePosdespachoNacional.jsf'
    response = r.get(url)
    df_yesterday = pd.read_html(response.text, skiprows=1, index_col=0, header=0)[0]

    soup = BeautifulSoup(response.text, 'html.parser')
    yesterday_date = soup.select('#formPosdespacho:pickFechaInputDate')[0]['value']
    jsf_view_state = soup.select('#javax.faces.ViewState')[0]['value']

    yesterday = arrow.get(yesterday_date, 'DD/MM/YYYY', tzinfo=TIMEZONE)
    today = yesterday.shift(days=+1)

    data = [
        ('formPosdespacho', 'formPosdespacho'),
        ('formPosdespacho:pickFechaInputDate', today.format(DATE_FORMAT)),
        ('formPosdespacho:pickFechaInputCurrentDate', today.format(MONTH_FORMAT)),
        ('formPosdespacho:j_id35.x', ''),
        ('formPosdespacho:j_id35.y', ''),
        ('javax.faces.ViewState', jsf_view_state),
    ]
    response = r.post(url, cookies={}, data=data)
    df_today = pd.read_html(response.text, skiprows=1, index_col=0)[0]

    ydata = df_to_data(country_code, yesterday, df_yesterday)
    tdata = df_to_data(country_code, today, df_today)
    production = ydata + tdata
    unknown_plants()

    return production


def fetch_exchange(country_code1='CR', country_code2='NI', session=None):
    """Requests the last known power exchange (in MW) between two regions

    Arguments:
    country_code1           -- the first country code
    country_code2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }

    where net flow is from DK into NO
    """
    sorted_country_codes = '->'.join(sorted([country_code1, country_code2]))

    df = pd.read_csv('http://www.enteoperador.org/newsite/flash/data.csv', index_col=False)

    if sorted_country_codes == 'CR->NI':
        flow = df['NICR'][0]
    elif sorted_country_codes == 'CR->PA':
        flow = -1 * df['CRPA'][0]
    else:
        raise NotImplementedError('This exchange pair is not implemented')

    data = {
        'datetime': arrow.now(TIMEZONE).datetime,
        'sortedCountryCodes': sorted_country_codes,
        'netFlow': flow,
        'source': 'enteoperador.org'
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange() ->')
    print(fetch_exchange())
