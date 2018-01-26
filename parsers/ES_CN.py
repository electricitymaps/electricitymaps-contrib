#!/usr/bin/env python3

# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import (ElHierro, GranCanaria, Gomera, LanzaroteFuerteventura,
                        LaPalma, Tenerife)
from parsers.lib.exceptions import ParserException


def fetch_island_data(country_code, session):
    if country_code == 'ES-CN-FVLZ':
        lanzarote_fuerteventura_data = LanzaroteFuerteventura(session).get_all()
        if not lanzarote_fuerteventura_data:
            raise ParserException(country_code, "LanzaroteFuerteventura not response")
        else:
            return lanzarote_fuerteventura_data
    else:
        raise ParserException(country_code, 'Can\'t read this country code {0}'.format(country_code))


def fetch_consumption(country_code='ES-CN', session=None):
    ses = session or Session()
    island_data = fetch_island_data(country_code, ses)
    data = []
    for response in island_data:
        response_data = {
            'countryCode': country_code,
            'datetime': get(response.timestamp).datetime,
            'consumption': response.demand,
            'source': 'demanda.ree.es'
        }

        data.append(response_data)

    return data


def fetch_production(country_code, session=None):
    ses = session or Session()
    island_data = fetch_island_data(country_code, ses)
    data = []

    for response in island_data:
        if response.production() > 0:
            response_data = {
                'countryCode': country_code,
                'datetime': get(response.timestamp).datetime,
                'production': {
                    'coal': 0.0,
                    'gas': round(response.gas + response.combined, 2),
                    'solar': round(response.solar, 2),
                    'oil': round(response.vapor + response.diesel, 2),
                    'wind': round(response.wind, 2),
                    'hydro': round(response.hydraulic, 2),
                    'biomass': 0.0,
                    'nuclear': 0.0,
                    'geothermal': 0.0,
                    'unknown': 0.0
                },
                'storage': {
                    'hydro': 0.0,
                    'battery': 0.0
                },
                'source': 'demanda.ree.es',
            }

            data.append(response_data)

    return data


if __name__ == '__main__':
    session = Session
    print(fetch_consumption('ES-CN-FVLZ', session))
    print(fetch_production('ES-CN-FVLZ', session))
