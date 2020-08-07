#!/usr/bin/env python3

import arrow
import json
import logging
import os
import math

import pandas as pd
import requests

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

EXCHANGE = {
    'FR-ARA': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_auvergne_rhone_alpes'
            }
        },
    'FR-BFC': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_bourgogne_franche_comte',
            'export': 'flux_physiques_de_bourgogne_franche_comte_vers_grand_est'
            }
        },
    'FR-BRE': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_bretagne',
            'export': 'flux_physiques_de_bretagne_vers_grand_est'
            }
        },
    'FR-CVL': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_centre_val_de_loire',
            'export': 'flux_physiques_de_centre_val_de_loire_vers_grand_est'
            }
        },
    'FR-GES': {
        # BE to GB inclusive import and export are the other way around to allow for zones to be aligned in alphabetical order
        'BE': {
            'import': 'flux_physiques_de_grand_est_vers_belgique',
            'export': 'flux_physiques_belgique_vers_grand_est'
        },
        'CH': {
            'import': 'flux_physiques_de_grand_est_vers_suisse',
            'export': 'flux_physiques_suisse_vers_grand_est'
        },
        'DE': {
            'import': 'flux_physiques_de_grand_est_vers_allemagne',
            'export': 'flux_physiques_allemagne_vers_grand_est'
        },
        'ES': {
            'import': 'flux_physiques_de_grand_est_vers_espagne',
            'export': 'flux_physiques_espagne_vers_grand_est'
        },
        # normal again
        'GB': {
            'import': 'flux_physiques_royaume_uni_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_royaume_uni'
        },
        'IT': {
            'import': 'flux_physiques_italie_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_italie'
        },
        'LU': {
            'import': 'flux_physiques_luxembourg_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_luxembourg'
        },
        'FR-HDF': {
            'import': 'flux_physiques_de_hauts_de_france_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_hauts_de_france'
        },
        'FR-IDF': {
            'export': 'flux_physiques_de_grand_est_vers_ile_de_france'
        },
        'FR-NOR': {
            'import': 'flux_physiques_de_normandie_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_normandie'
        },
        'FR-NAQ': {
            'import': 'flux_physiques_de_nouvelle_aquitaine_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_nouvelle_aquitaine'
        },
        'FR-OCC': {
            'export': 'flux_physiques_de_grand_est_vers_occitanie'
        },
        'FR-PDL': {
            'import': 'flux_physiques_de_pays_de_la_loire_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_pays_de_la_loire'
        },
        'FR-PAC': {
            'import': 'flux_physiques_de_paca_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_paca'
        }
    }
}


def is_not_nan_and_truthy(v):
    if isinstance(v, float) and math.isnan(v):
        return False
    return bool(v)

def fetch(zone_key, session=None, target_datetime=None):
    if target_datetime:
        to = arrow.get(target_datetime, 'Europe/Paris')
    else:
        to = arrow.now(tz='Europe/Paris')

    # setup request
    r = session or requests.session()
    formatted_from = to.shift(days=-1).format('YYYY-MM-DDTHH:mm')
    formatted_to = to.format('YYYY-MM-DDTHH:mm')

    params = {
        'dataset': 'eco2mix-regional-tr',
        'q': 'date_heure >= {} AND date_heure <= {}'.format(
            formatted_from, formatted_to),
        'timezone': 'Europe/Paris',
        'rows': 100,
        'refine.libelle_region': FR_REGIONS[zone_key]
    }

    # make request and create dataframe with response
    response = r.get(API_ENDPOINT, params=params)
    data = json.loads(response.content)
    data = [d['fields'] for d in data['records']]
    df = pd.DataFrame(data)

    return df


def fetch_production(zone_key, session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):

    df = fetch(zone_key, session=session, target_datetime=target_datetime)

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

def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=logging.getLogger(__name__)):

    # two scenarios: zone_key1 either a French region or another EU country
    if zone_key1 in FR_REGIONS.keys():
        df = fetch(zone_key1, session=session, target_datetime=target_datetime)
        exchange_zone = EXCHANGE[zone_key1][zone_key2]
    else:
        df = fetch(zone_key2, session=session, target_datetime=target_datetime)
        exchange_zone = EXCHANGE[zone_key2][zone_key1]

    # cleaning data
    value_columns = list(exchange_zone.values())
    df = df.loc[:, ['date_heure'] + value_columns]

    x_export = exchange_zone['export']
    if 'import' not in exchange_zone:
        x_import = 'default_column'
        df[x_import] = 0
    else:
        x_import = exchange_zone['import']

    df.dropna(how='any', inplace=True)
    df.replace({x_import: "-", x_export: "-"}, 0, inplace=True)

    # converting data to float
    df[value_columns] = df[value_columns].astype(float)
    df['net_flow'] = (df[x_export] + df[x_import]) * -1

    # compiling datapoints
    datapoints = list()

    for row in df.iterrows():
        if row[1]['net_flow'] == 0:
          net_flow = 0
        else:
          net_flow = row[1]['net_flow']

        datapoint = {
            'sortedZoneKeys': '->'.join(sorted([zone_key1, zone_key2])),
            'datetime': arrow.get(row[1]['date_heure']).datetime,
            'netFlow': net_flow,
            'source': 'opendata.reseaux-energies.fr'
        }

        datapoints.append(datapoint)

    datapoints = sorted(datapoints, key=lambda x: x['datetime'])

    return datapoints


# enter any of the regional zone keys when calling method
if __name__ == '__main__':
    # print(fetch_production('FR-OCC'))
    print(fetch_exchange('FR-GES', 'GB'))
