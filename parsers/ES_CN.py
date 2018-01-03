#!/usr/bin/env python3

# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import (ElHierro, GranCanaria, Gomera, LanzaroteFuerteventura,
                        LaPalma, Tenerife)
from parsers.lib.exceptions import ParserException


def fetch_islands_data(country_code, session):
    data = {}

    el_hierro_data = ElHierro(session).get_all()
    if not el_hierro_data:
        raise ParserException(country_code, "ElHierro not response")
    else:
        data.update({'el_hierro': el_hierro_data})

    gran_canaria_data = GranCanaria(session).get_all()
    if not gran_canaria_data:
        raise ParserException(country_code, "GranCanaria not response")
    else:
        data.update({'gran_canaria': gran_canaria_data})

    gomera_data = Gomera(session).get_all()
    if not gomera_data:
        raise ParserException(country_code, "Gomera not response")
    else:
        data.update({'gomera': gomera_data})

    lanzarote_fuerteventura_data = LanzaroteFuerteventura(session).get_all()
    if not lanzarote_fuerteventura_data:
        raise ParserException(country_code, "LanzaroteFuerteventura not response")
    else:
        data.update({'lanzarote_fuerteventura': lanzarote_fuerteventura_data})

    la_palma_data = LaPalma(session).get_all()
    if not la_palma_data:
        raise ParserException(country_code, "LaPalma not response")
    else:
        data.update({'la_palma': la_palma_data})

    tenerife_data = Tenerife(session).get_all()
    if not tenerife_data:
        raise ParserException(country_code, "Tenerife not response")
    else:
        data.update({'tenerife': tenerife_data})

    return data


def fetch_consumption(country_code='ES-CN', session=None):
    ses = session or Session()

    islands_data = fetch_islands_data(country_code, ses)

    consumption_data = {}

    el_hierro_island_data = islands_data['el_hierro']
    for response in el_hierro_island_data:
        consumption_datetime = get(response.timestamp).datetime
        consumption = response.demand
        consumption_data.update({consumption_datetime: consumption})

    for island, island_data in islands_data.items():
        if not island == 'el_hierro':
            for response in island_data:
                consumption_datetime = get(response.timestamp).datetime
                consumption = response.demand
                if consumption_datetime in consumption_data:
                    consumption = consumption_data[consumption_datetime] + consumption
                    consumption_data.update({consumption_datetime: consumption})

    data = []

    for datetime, demand in consumption_data.items():
        response_data = {
            'countryCode': country_code,
            'datetime': datetime,
            'consumption': round(demand, 2),
            'source': 'demanda.ree.es'
        }

        data.append(response_data)

    return data


def fetch_production(country_code='ES-CN', session=None):
    ses = session or Session()

    islands_data = fetch_islands_data(country_code, ses)

    production_data = {}

    el_hierro_island_data = islands_data['el_hierro']
    for response in el_hierro_island_data:
        if response.production() > 0:
            production_datetime = get(response.timestamp).datetime
            production = {
                'gas': response.gas + response.combined,
                'oil': response.vapor + response.diesel,
                'solar': response.solar,
                'wind': response.wind,
                'hydro': 0.0,
                'storage': -response.hydraulic
            }
            production_data.update({production_datetime: production})

    for island, island_data in islands_data.items():
        if not island == 'el_hierro':
            for response in island_data:
                production_datetime = get(response.timestamp).datetime
                if production_datetime in production_data:
                    if response.production() <= 0:
                        production_data.pop(production_datetime, None)
                    else:
                        production = production_data[production_datetime]
                        production = {
                            'gas': production['gas'] + response.gas + response.combined,
                            'oil': production['oil'] + response.vapor + response.diesel,
                            'solar': production['solar'] + response.solar,
                            'wind': production['wind'] + response.wind,
                            'hydro': production['hydro'] + response.hydraulic,
                            'storage': production['storage']
                        }
                        production_data.update({production_datetime: production})

    data = []

    for datetime, production in production_data.items():
        response_data = {
            'countryCode': country_code,
            'datetime': datetime,
            'production': {
                'coal': 0.0,
                'gas': round(production['gas'], 2),
                'solar': round(production['solar'], 2),
                'oil': round(production['oil'], 2),
                'wind': round(production['wind'], 2),
                'hydro': round(production['hydro'], 2),
                'biomass': 0.0,
                'nuclear': 0.0,
                'geothermal': 0.0,
                'unknown': 0.0
            },
            'storage': {
                'hydro': round(production['storage'], 2)
            },
            'source': 'demanda.ree.es'
        }

        data.append(response_data)

    return data


if __name__ == '__main__':
    session = Session
    print(fetch_consumption('ES-CN', session))
    print(fetch_production('ES-CN', session))
