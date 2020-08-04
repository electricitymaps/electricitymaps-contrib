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

os.environ['RESEAUX_ENERGIES_TOKEN']='8286b3219dbedb0c74bbab52ef6a268fcaf79423f7b2deb727a6e803'

API_ENDPOINT = 'https://opendata.reseaux-energies.fr/api/records/1.0/search/'

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
        'BE': {
            'import': 'flux_physiques_belgique_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_belgique'
        },
        'CH': {
            'import': 'flux_physiques_suisse_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_suisse'
        },
        'DE': {
            'import': 'flux_physiques_allemagne_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_allemagne'
        },
        'ES': {
            'import': 'flux_physiques_espagne_vers_grand_est',
            'export': 'flux_physiques_de_grand_est_vers_espagne'
        },
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
        }
    },
    'FR-HDF': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_hauts_de_france',
            'export': 'flux_physiques_de_hauts_de_france_vers_grand_est'
            }
        },
    'FR-IDF': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_ile_de_france'
            }
        },
    'FR-NOR': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_normandie',
            'export': 'flux_physiques_de_normandie_vers_grand_est'
            }
        },
    'FR-NAQ': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_nouvelle_aquitaine',
            'export': 'flux_physiques_de_nouvelle_aquitaine_vers_grand_est'
            }
        },
    'FR-OCC': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_occitanie'
            }
        },
    'FR-PDL': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_pays_de_la_loire',
            'export': 'flux_physiques_de_pays_de_la_loire_vers_grand_est'
            }
        },
    'FR-PAC': {
        'FR-GES': {
            'import': 'flux_physiques_de_grand_est_vers_paca',
            'export': 'flux_physiques_de_paca_vers_grand_est'
            }
        }
}

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


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=logging.getLogger(__name__)):

    df = fetch(zone_key1, session=session, target_datetime=target_datetime)

##############################################
    # filter out desired columns and convert values to float
    exchange_zone = EXCHANGE[zone_key1][zone_key2]

    value_columns = list(exchange_zone.values())
    df = df.loc[:, ['date_heure'] + value_columns]

    x_import = exchange_zone['import']

    if 'export' not in exchange_zone:
        x_export = 'default_column'
        df[x_export] = 0
    else:
        x_export = exchange_zone['export']

    df.dropna(how='any', inplace=True)
    df.replace({x_import: "-", x_export: "-"}, 0, inplace=True)

    # converting data to float
    df[value_columns] = df[value_columns].astype(float)

    df['net_flow'] = (df[x_export] + df[x_import]) * -1


########################################################
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

if __name__ == '__main__':


  print(fetch_exchange('FR-ARA', 'FR-GES'))
