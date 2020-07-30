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

# Setting env variable
os.environ['RESEAUX_ENERGIES_TOKEN']='8286b3219dbedb0c74bbab52ef6a268fcaf79423f7b2deb727a6e803'

# # taken from FR.py
API_ENDPOINT = 'https://opendata.reseaux-energies.fr/api/records/1.0/search/'

MAP_GENERATION = {
    'nucleaire': 'nuclear',
    'thermique': 'thermal', #lump sum for coal, oil, gas as breakdown not available at regional level
    'eolien': 'wind',
    'solaire': 'solar',
    'hydraulique': 'hydro',
    'bioenergies': 'biomass'
}


# # Define all RTE French regional zone-key <-> domain mapping
# RTE_FR_REGION_MAPPINGS = {
#   'FR-ARA': 'Auvergne-Rh%C3%B4ne-Alpes',
#   'FR-BFC': 'Bourgogne-Franche-Comt%C3%A9',
#   'FR-BRE': 'Bretagne',
#   'FR-CVL': 'Centre-Val+de+Loire',
#   'FR-GES': 'Grand-Est',
#   'FR-HDF': 'Hauts-de-France',
#   'FR-IDF': 'Ile-de-France',
#   'FR-NOR': 'Normandie',
#   'FR-NAQ': 'Nouvelle-Aquitaine',
#   'FR-OCC': 'Occitanie',
#   'FR-PDL': 'Pays+de+la+Loire',
#   'FR-PAC': 'Provence-Alpes-Côte+d%27Azur'
# }

def is_not_nan_and_truthy(v):
    if isinstance(v, float) and math.isnan(v):
        return False
    return bool(v)

# NOTE: Changed zone key from FR to FR-OCC (need to make this dynamic now)
def fetch_production(zone_key='FR-OCC', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    if target_datetime:
        to = arrow.get(target_datetime, 'Europe/Paris')
    else:
        to = arrow.now(tz='Europe/Paris')

    # setup request
    r = session or requests.session()
    formatted_from = to.shift(days=-1).format('YYYY-MM-DDTHH:mm')
    formatted_to = to.format('YYYY-MM-DDTHH:mm')

    # dataset changed to regional regional + refine search parameter for region
    params = {
        'dataset': 'eco2mix-regional-tr',
        'q': 'date_heure >= {} AND date_heure <= {}'.format(
            formatted_from, formatted_to),
        'timezone': 'Europe/Paris',
        'rows': 100,
        'refine.libelle_region': 'Occitanie'
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

    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys())
    missing_fuels = [v for v in value_columns if v not in df.columns]
    present_fuels = [v for v in value_columns if v in df.columns]
    if len(missing_fuels) == len(value_columns):
        logger.warning('No fuels present in the API response')
        return list()
    elif len(missing_fuels) > 0:
        mf_str = ', '.join(missing_fuels)
        logger.warning('Fuels [{}] are not present in the API '
                       'response'.format(mf_str))

    df = df.loc[:, ['date_heure'] + present_fuels]
    df[present_fuels] = df[present_fuels].astype(float)

    datapoints = list()
    for row in df.iterrows():
        production = dict()
        for key, value in MAP_GENERATION.items():
            if key not in present_fuels:
                continue

            if -50 < row[1][key] < 0:
                # set small negative values to 0
                logger.warning('Setting small value of %s (%s) to 0.' % (key, value))
                production[value] = 0
            else:
                production[value] = row[1][key]
        datapoint = {
            'zoneKey': zone_key,
            'datetime': arrow.get(row[1]['date_heure']).datetime,
            'production': production,
            'source': 'opendata.reseaux-energies.fr'
        }
        datapoint = validate(datapoint, logger, required=['nuclear', 'hydro', 'thermal']) # changed validation of gas to hydro
        datapoints.append(datapoint)

    max_diffs = {
        'hydro': 1600,
        'solar': 1000, # was 500 before
        'thermal': 2000, # changed this to hypothetical value
        'wind': 1000,
        'nuclear': 1300,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints

if __name__ == '__main__':
    print(fetch_production())





