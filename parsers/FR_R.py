#!/usr/bin/env python3

import arrow
import json
from logging import Logger, getLogger
import os
import math

import numpy as np
import pandas as pd
import requests

from datetime import datetime, timedelta
from io import BytesIO
from unidecode import unidecode
from zipfile import ZipFile

from electricitymap.contrib.config import EXCHANGES_CONFIG

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from .lib.validation import validate, validate_production_diffs

API_ENDPOINT = 'https://eco2mix.rte-france.com/curves/eco2mixDl'

# note: thermal lump sum for coal, oil, gas as breakdown not available at regional level
MAP_GENERATION = {
    'Nucléaire': 'nuclear',
    'Thermique': 'unknown',
    'Eolien': 'wind',
    'Solaire': 'solar',
    'Hydraulique': 'hydro',
    'Bioénergies': 'biomass'
}

MAP_STORAGE = {
    'Pompage': 'hydro',
}

# define all RTE French regional zone-key <-> domain mapping
ZONE_IDENTIFIERS = {
    'BE': 'Belgique',
    'CH': 'Suisse',
    'DE': 'Allemagne',
    'ES': 'Espagne',
    'GB': 'Royaume-Uni',
    'IT-NO': 'Italie',
    'LU': 'Luxembourg',
    'FR-ACA': 'Grand-Est',
    'FR-ARA': 'Auvergne-Rhône-Alpes',
    'FR-ALP': 'Nouvelle-Aquitaine',
    'FR-BFC': 'Bourgogne-Franche-Comté',
    'FR-BRE': 'Bretagne',
    'FR-CEN': 'Centre-Val de Loire',
    'FR-NPP': 'Hauts-de-France',
    'FR-IDF': 'Ile-de-France',
    'FR-NOR': 'Normandie',
    'FR-LRM': 'Occitanie',
    'FR-PLO': 'Pays de la Loire',
    'FR-PAC': 'Provence-Alpes-Côte d\'Azur'
}

# validations for each region
VALIDATIONS = {
    'FR-ACA': ['unknown', 'nuclear', 'hydro'],
    'FR-ARA': ['unknown', 'nuclear', 'hydro'],
    'FR-ALP': ['nuclear', 'hydro'],
    'FR-BFC': ['wind'],
    'FR-BRE': ['unknown', 'wind'],
    'FR-CEN': ['nuclear', 'wind'],
    'FR-NPP': ['unknown', 'nuclear'],
    'FR-IDF': ['unknown'],
    'FR-NOR': ['unknown', 'nuclear'],
    'FR-LRM': ['nuclear', 'hydro'],
    'FR-PLO': ['unknown', 'wind'],
    'FR-PAC': ['unknown', 'hydro'],
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

    assert 'FR-' in zone_key

    # setup request
    r = session or requests.session()

    params = {
        'date': to.floor('day').format('DD/MM/YYYY'),
        'region': zone_key.replace('FR-', ''),
    }
    response = r.get(API_ENDPOINT, params=params)
    response.raise_for_status()
    # Write content to in-memory zip file
    buf = BytesIO()
    buf.write(response.content)
    buf.seek(0)
    # Decode zip and extract XLS
    zip = ZipFile(buf)
    with zip.open(zip.namelist()[0], 'r') as file:
        df = pd.read_csv(file, sep='\t', encoding='latin-1', nrows=4*24, na_values=['-', 'ND'])

    # Add datetime
    df['date_heure'] = df['Date'] + ' ' + df['Heures']
    df = df.set_index('date_heure')
    assert not df.index.isna().any(), 'date_heure can\'t have any nan'

    return df


@refetch_frequency(timedelta(days=1))
def fetch_production(zone_key, session=None, target_datetime=None,
                     logger: Logger = getLogger(__name__)):

    df = fetch(zone_key, session=session, target_datetime=target_datetime)

    # filter out desired columns and convert values to float
    value_columns = list(MAP_GENERATION.keys()) + list(MAP_STORAGE.keys()) + [f'tch_{x}' for x in MAP_GENERATION.keys()]
    missing_columns = [v for v in value_columns if v not in df.columns]
    present_columns = [v for v in value_columns if v in df.columns]
    assert len(missing_columns) != len(value_columns), 'All columns of interest are missing from the API response'

    if len(missing_columns) > 0:
        mf_str = ', '.join(missing_columns)
        logger.warning('Columns [{}] are not present in the API '
                       'response'.format(mf_str))
        # note this happens and is ok as not all French regions have all fuels.

    df = df.loc[:, present_columns]
    df[present_columns] = df[present_columns].astype(float)

    datapoints = list()
    for _, row in df.iterrows():
        production = dict()
        storage = dict()
        capacity = dict()

        for key, value in MAP_GENERATION.items():
            if key not in present_columns:
                continue

            if -50 < row[key] < 0:
                # set small negative values to 0
                logger.warning('Setting small value of %s (%s) to 0.' % (key, value))
                production[value] = 0
            else:
                production[value] = None if np.isnan(row[key]) else row[key]

            # # Capacity
            # load_factor = row[f'tch_{key}'] / 100.0
            # # We can't estimate capacity if load factor is too small
            # if load_factor > 0.05:
            #     capacity[value] = round(row[key] / load_factor)

        for key, value in MAP_STORAGE.items():
            if key not in present_columns:
                continue
            else:
                # Note: in the data, negative value means storage,
                # which is the opposite of our convention
                storage[value] = None if np.isnan(row[key]) else -1 * row[key]

        # if all production values are null, ignore datapoint
        if not any([is_not_nan_and_truthy(v)
                    for k, v in production.items()]):
            continue

        datapoint = {
            'zoneKey': zone_key,
            'datetime': arrow.get(row.name, tzinfo='Europe/Paris').datetime,
            'production': production,
            'storage': storage,
            'capacity': capacity,
            'source': 'opendata.reseaux-energies.fr'
        }
        # validations responsive to region
        datapoint = validate(datapoint, logger, required=VALIDATIONS[zone_key])
        datapoints.append(datapoint)

    max_diffs = {
        'hydro': 1600,
        'solar': 1000, # was 500 before
        'unknown': 2000, # thermal
        'wind': 1000,
        'nuclear': 1300,
    }

    datapoints = validate_production_diffs(datapoints, max_diffs, logger)

    return datapoints


@refetch_frequency(timedelta(days=1))
def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger: Logger = getLogger(__name__)):

    # two scenarios: zone_key1 either a French region or another EU country
    # we can't fetch another EU country, so fetch the other region
    df = fetch(zone_key1 if 'FR-' in zone_key1 else zone_key2, session=session, target_datetime=target_datetime)

    if df.empty:
        return []

    # Verify that all columns are indeed part of exchange_zone
    # to make sure we don't miss a single one
    logger.debug(f'Calculating {zone_key1} -> {zone_key2}')

    series = None # Resulting series

    def match_region(str1, str2):
        str1, str2 = [
            # Strip accents
            unidecode(x.replace('PACA', 'Provence-Alpes-Côte d\'Azur').lower().replace('-', ' '))
        for x in (str1, str2)]
        return str1 == str2

    for key in df.filter(like='Flux physiques').columns:
        # e.g. flux_physiques_de_nouvelle_aquitaine_vers_auvergne_rhone_alpes

        # Ignore some testing columns
        if '.1' in key:
            continue

        label1, label2 = key.replace('Flux physiques d\'', '').replace('Flux physiques de ', '').replace('Flux physiques ', '').split(' vers ')
        if label1 == '': label1 = ZONE_IDENTIFIERS[zone_key1]
        if label2 == '': label2 = ZONE_IDENTIFIERS[zone_key2]
        zone_1_matches = [k for k, v in ZONE_IDENTIFIERS.items() if match_region(v, label1)]
        zone_2_matches = [k for k, v in ZONE_IDENTIFIERS.items() if match_region(v, label2)]

        if df[key].abs().sum() > 0:
            assert len(zone_1_matches) > 0, f"key '{key}' doesn't correspond to a known exchange ({label1} has no ZONE_IDENTIFIERS matches)"
            assert len(zone_2_matches) > 0, f"key '{key}' doesn't correspond to a known exchange ({label2} has no ZONE_IDENTIFIERS matches)"
            # Verify that the exchange is in config
            exchange_key = '->'.join(sorted([zone_1_matches[0], zone_2_matches[0]]))
            assert exchange_key in EXCHANGES_CONFIG, f'Exchange key {exchange_key} is not in exchanges.json'

        if not zone_1_matches or not zone_2_matches: continue

        if zone_1_matches[0] == zone_2_matches[0]:
            # Ignore flow to self
            continue

        if zone_1_matches[0] in [zone_key1, zone_key2] and zone_2_matches[0] in [zone_key1, zone_key2]:
            # We found the right column
            if zone_1_matches[0] == zone_key1:
                assert zone_2_matches[0] == zone_key2
                multiplier = 1 # Same direction as asked
            else:
                assert zone_2_matches[0] == zone_key1
                multiplier = -1 # Flow will need to be reversed

            if series is None:
                series = df[key] * multiplier
            else:
                # When adding, make sure that NaNs + <value> yields <value>
                series = series.add(multiplier * df[key], fill_value=0)

    if series is None:
        raise ParserException("Couldn\'t find proper interconnector column")

    # RTE doesn't report 0 when data is known, so we have to
    # assume that any nan is actually 0
    series = series.fillna(0)

    # compiling datapoints
    datapoints = [
        {
            'sortedZoneKeys': '->'.join(sorted([zone_key1, zone_key2])),
            'datetime': arrow.get(index, tzinfo='Europe/Paris').datetime,
            'netFlow': value,
            'source': 'opendata.reseaux-energies.fr'
        }
    for index, value in series.sort_index().iteritems()]

    now = arrow.now(tz='Europe/Paris').datetime
    return list(filter(lambda d: d['datetime'] <= now, datapoints))


# enter any of the regional zone keys when calling method
if __name__ == '__main__':
    # print(fetch_production('FR-LRM'))
    print("J. rocks!")
    print(fetch_exchange('FR-ACA', 'GB'))
