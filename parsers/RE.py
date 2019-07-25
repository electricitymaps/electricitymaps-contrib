#!/usr/bin/env python3
# coding=utf-8

import arrow
import json
import logging
import requests

API_ENDPOINT = 'https://opendata-reunion.edf.fr/api/records/1.0/search/'

MAP_GENERATION = {
    'gas': 'biogaz',
    'oil': 'thermique',
    'wind': 'eolien',
    'biomass': 'bioenergies',
    'hydro': 'hydraulique',
    'solar': 'photovoltaique',
    'solar_with_storage': 'photovoltaique_avec_stockage',
    'bagasse_coal': 'bagasse_charbon'
}

# Depending on the month, this correspond more or less to bagasse or coal.
# This map is an clumsy approximation using harvesting period and annual
# percentage of biomass used. Here, we use  17.17% for this percentage
# (https://fr.wikipedia.org/wiki/Usine_de_Bois_Rouge &
# https://fr.wikipedia.org/wiki/Usine_du_Gol)
MAP_GENERATION_BAGASSE_COAL = {
    1: {'coal': 1, 'biomass': 0},
    2: {'coal': 1, 'biomass': 0},
    3: {'coal': 1, 'biomass': 0},
    4: {'coal': 1, 'biomass': 0},
    5: {'coal': 1, 'biomass': 0},
    6: {'coal': 1, 'biomass': 0},
    7: {'coal': 0.77, 'biomass': 0.23},
    8: {'coal': 0.6, 'biomass': 0.4},
    9: {'coal': 0.6, 'biomass': 0.4},
    10: {'coal': 0.6, 'biomass': 0.4},
    11: {'coal': 0.6, 'biomass': 0.4},
    12: {'coal': 0.77, 'biomass': 0.23},
}


def fetch_production(zone_key='RE', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):

    if target_datetime:
        raise NotImplementedError('There is no historical data')
    else:
        to = arrow.now(tz='Indian/Reunion')

    r = session or requests.session()

    params = {
        'dataset': 'prod-electricite-temps-reel',
        'timezone': 'Indian/Reunion',
        'sort': 'date',
        'rows': 288
    }
    response = r.get(API_ENDPOINT, params=params)
    data = json.loads(response.content)
    datapoints = []

    for i in range(0, len(data['records'])):
        record = data['records'][i]
        # All biomass
        biomass = 0
        if(MAP_GENERATION['bagasse_coal'] in record['fields']):
            biomass += MAP_GENERATION_BAGASSE_COAL[to.month]['biomass'] * record['fields'][MAP_GENERATION['bagasse_coal']]
        if(MAP_GENERATION['biomass'] in record['fields']):
            biomass += record['fields'][MAP_GENERATION['biomass']]

        wind = 0
        solar = 0
        gas = 0
        coal = 0

        # Other
        if(MAP_GENERATION['wind'] in record['fields']):
            wind = record['fields'][MAP_GENERATION['wind']]
        if(MAP_GENERATION['solar'] in record['fields']):
            solar = record['fields'][MAP_GENERATION['solar']]
        if(MAP_GENERATION['gas'] in record['fields']):
            gas = record['fields'][MAP_GENERATION['gas']]
        if(MAP_GENERATION['oil'] in record['fields']):
            oil = record['fields'][MAP_GENERATION['oil']]
        if(MAP_GENERATION['bagasse_coal'] in record['fields']):
            coal = MAP_GENERATION_BAGASSE_COAL[to.month]['coal'] * record['fields'][MAP_GENERATION['bagasse_coal']]

        # Storages
        solar_storage = 0
        hydro_storage = 0
        hydro = 0
        if(MAP_GENERATION['solar_with_storage'] in record['fields']):
            if(record['fields'][MAP_GENERATION['solar_with_storage']] < 0):
                solar_storage = record['fields'][MAP_GENERATION['solar_with_storage']]
            else:
                solar += record['fields'][MAP_GENERATION['solar_with_storage']]
        if(MAP_GENERATION['hydro'] in record['fields']):
            if(record['fields'][MAP_GENERATION['hydro']] < 0):
                hydro_storage = record['fields'][MAP_GENERATION['hydro']]
            else:
                hydro = record['fields'][MAP_GENERATION['hydro']]

        datapoints.append({
            'zoneKey': 'RE',
            'datetime': record['fields']['date'],
            'production': {
                'biomass': biomass,
                'coal': coal,
                'gas': gas,
                'hydro': hydro,
                'oil': oil,
                'solar': solar,
                'wind': wind,
            },
            'storage': {
                'solar': solar_storage,
                'hydro': hydro_storage,
            },
            'source': 'opendata-reunion.edf.fr'
        })

    return datapoints


def fetch_consumption(zone_key='RE', session=None, target_datetime=None,
                      logger=logging.getLogger(__name__)):
    raise NotImplementedError('This parser is not able to give consumption')


def fetch_price(zone_key='RE', session=None, target_datetime=None,
                logger=logging.getLogger(__name__)):
    raise NotImplementedError('This parser is not able to retrieve prices')


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""
    print('fetch_production() ->')
    print(fetch_production())
