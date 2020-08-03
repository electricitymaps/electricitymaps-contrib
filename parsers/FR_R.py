#!/usr/bin/env python3

import arrow
import json
import logging
import os
import math

import pandas as pd
import requests
# import xml.etree.ElementTree as ET

from lib.validation import validate, validate_production_diffs

# setting env variable
os.environ['RESEAUX_ENERGIES_TOKEN']='8286b3219dbedb0c74bbab52ef6a268fcaf79423f7b2deb727a6e803'

API_ENDPOINT = 'https://opendata.reseaux-energies.fr/api/records/1.0/search/'

# note: thermal lump sum for coal, oil, gas as breakdown not available at regional level
MAP_GENERATION = {
    'nucleaire': 'nuclear',
    'thermique': 'thermal',
    'eolien': 'wind',
    'solaire': 'solar',
    'hydraulique': 'hydro',
    'bioenergies': 'biomass'
}

MAP_STORAGE = {
    'pompage': 'hydro',
}

# define all RTE French regional zone-key <-> domain mapping
FR_REGIONS = {
    'FR-ARA': 'Auvergne-Rhône-Alpes',
    'FR-BFC': 'Bourgogne-Franche-Comté',
    'FR-BRE': 'Bretagne',
    'FR-CVL': 'Centre-Val de Loire',
    'FR-GES': 'Grand-Est',
    'FR-HDF': 'Hauts-de-France',
    'FR-IDF': 'Ile-de-France',
    'FR-NOR': 'Normandie',
    'FR-NAQ': 'Nouvelle-Aquitaine',
    'FR-OCC': 'Occitanie',
    'FR-PDL': 'Pays de la Loire',
    'FR-PAC': 'Provence-Alpes-Côte d\'Azur'
}

# validations for each region
VALIDATIONS = {
    'FR-ARA': ['thermal', 'nuclear', 'hydro'],
    'FR-BFC': ['wind'],
    'FR-BRE': ['thermal', 'wind'],
    'FR-CVL': ['nuclear', 'wind'],
    'FR-GES': ['thermal', 'nuclear', 'hydro'],
    'FR-HDF': ['thermal', 'nuclear'],
    'FR-IDF': ['thermal'],
    'FR-NOR': ['thermal', 'nuclear'],
    'FR-NAQ': ['nuclear', 'hydro'],
    'FR-OCC': ['nuclear', 'hydro'],
    'FR-PDL': ['thermal', 'wind'],
    'FR-PAC': ['thermal', 'hydro'],
}

def is_not_nan_and_truthy(v):
    if isinstance(v, float) and math.isnan(v):
        return False
    return bool(v)

# need to input zone_key when fetching production
def fetch_production(zone_key, session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):

    if target_datetime:
        to = arrow.get(target_datetime, 'Europe/Paris')
    else:
        to = arrow.now(tz='Europe/Paris')

    zone_key=zone_key

    # setup request
    r = session or requests.session()
    formatted_from = to.shift(days=-1).format('YYYY-MM-DDTHH:mm')
    formatted_to = to.format('YYYY-MM-DDTHH:mm')

    # dataset changed to regional + refine.libelle_region added
    params = {
        'dataset': 'eco2mix-regional-tr',
        'q': 'date_heure >= {} AND date_heure <= {}'.format(
            formatted_from, formatted_to),
        'timezone': 'Europe/Paris',
        'rows': 100,
        'refine.libelle_region': FR_REGIONS[zone_key]
    }

    if 'RESEAUX_ENERGIES_TOKEN' not in os.environ:
        raise Exception(
            'No RESEAUX_ENERGIES_TOKEN found! Please add it into secrets.env!')
    params['apikey'] = os.environ['RESEAUX_ENERGIES_TOKEN']

    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    data = json.loads(response.content)
    data = [d['fields'] for d in data['records']]
    df = pd.DataFrame(data)


#########################################
    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys()) + list(MAP_STORAGE.keys())
    missing_fuels = [v for v in value_columns if v not in df.columns]
    present_fuels = [v for v in value_columns if v in df.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning('No fuels present in the API response')
        return list()
    elif len(missing_fuels) > 0:
        mf_str = ', '.join(missing_fuels)
        logger.warning('Fuels [{}] are not present in the API '
                       'response'.format(mf_str))

    # note this happens and is ok as not all French regions have all fuels.

    df = df.loc[:, ['date_heure'] + present_fuels]
    df[present_fuels] = df[present_fuels].astype(float)

    datapoints = list()
    for row in df.iterrows():
        production = dict()
        storage = dict()

        for key, value in MAP_GENERATION.items():
            if key not in present_fuels:
                continue

            if -50 < row[1][key] < 0:
                # set small negative values to 0
                logger.warning('Setting small value of %s (%s) to 0.' % (key, value))
                production[value] = 0
            else:
                production[value] = row[1][key]

        for key, value in MAP_STORAGE.items():
            if key not in present_fuels:
                continue
            else:
                storage[value] = row[1][key]


        # if all production values are null, ignore datapoint
        if not any([is_not_nan_and_truthy(v)
                    for k, v in production.items()]):
            continue

        datapoint = {
            'zoneKey': zone_key,
            'datetime': arrow.get(row[1]['date_heure']).datetime,
            'production': production,
            'storage': storage,
            'source': 'opendata.reseaux-energies.fr'
        }
        # validations responsive to region
        datapoint = validate(datapoint, logger, required=VALIDATIONS[zone_key])
        datapoints.append(datapoint)

    max_diffs = {
        'hydro': 1600,
        'solar': 1000, # was 500 before
        'thermal': 2000, # added thermal
        'wind': 1000,
        'nuclear': 1300,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints


# enter any of the regional zone keys when calling method
if __name__ == '__main__':
    print(fetch_production('FR-OCC'))

