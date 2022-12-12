#!/usr/bin/env python3

import arrow
import json
from logging import Logger, getLogger
import os
import math

import numpy as np
import pandas as pd
import requests

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
# from io import BytesIO
# from unidecode import unidecode
# from zipfile import ZipFile

from electricitymap.contrib.config import EXCHANGES_CONFIG, ZONES_CONFIG

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from .lib.validation import validate, validate_production_diffs

# From RTE domain to EM domain
MAP_ZONES = {
    'France': 'FR',
    **{
        subzone.replace('FR-', ''): subzone
        for subzone in ZONES_CONFIG['FR'].get('subZoneNames', [])
    },
    'BE': 'BE',
    'CH': 'CH',
    'DE': 'DE',
    'ES': 'ES',
    'GB': 'GB',
    'IT': 'IT-NO',
    'LU': 'LU',
}

MAP_MODES = {
    'NuclÃ©aire': 'production.nuclear',
    'Thermique': 'production.unknown',
    'Eolien': 'production.wind',
    'Solaire': 'production.solar',
    'Hydraulique': 'production.hydro',
    'Bioénergies': 'production.biomass',
    'Consommation': 'consumption',
    'Autres': 'production.unknown',
    'Charbon': 'production.coal',
    'Fioul': 'production.oil',
    'Gaz': 'production.gas',

    'Pompage': 'storage.hydro',
    'Destockage': 'storage.hydro',
    'Batterie_Injection': 'storage.battery',
    'Batterie_Soutirage': 'storage.battery',
    'Stockage': 'storage.battery',

    'Solde': 'IGNORED',
    'Co2': 'IGNORED',
    'Taux de Co2': 'IGNORED',
    'PrÃ©visionJ': 'IGNORED',
    'PrÃ©visionJ-1': 'IGNORED',
}

# validations for each region
VALIDATIONS = {
    'FR-ARA': ['unknown', 'nuclear', 'hydro'],
}


def query_production(session=None, target_datetime=None):
    if target_datetime:
        date_to = arrow.get(target_datetime, 'Europe/Paris')
    else:
        date_to = arrow.now(tz='Europe/Paris')
    date_from = date_to.floor('day')

    URL = f"http://www.rte-france.com/getEco2MixXml.php?type=region&dateDeb={date_from.format('DD/MM/YYYY')}&dateFin={date_to.format('DD/MM/YYYY')}"
    r = session or requests.session()
    response = r.get(URL, verify=False)
    response.raise_for_status()
    return response.text


def parse_production_to_df(text):
    bs_content = BeautifulSoup(text, features="xml")
    # Flatten
    df = pd.DataFrame([
        {
            **valeur.attrs,
            **valeur.parent.attrs,
            **valeur.parent.parent.attrs,
            'value': valeur.contents[0]
        }
        for valeur in bs_content.find_all('valeur')
    ])
    # Add datetime
    df['datetime'] = pd.to_datetime(df['date']) + pd.to_timedelta(df['periode'].astype('int') * 15, unit='minute')
    df.datetime = df.datetime.dt.tz_localize("Europe/Paris")
    # Set index
    df = df.set_index('datetime').drop(['date', 'periode'], axis=1)
    # Remove invalid granularities
    df = df[df.granularite == 'Global'].drop('granularite', axis=1)
    # Create key (will crash if a mode is not in the map and ensures we coded this right)
    df['key'] = df.v.apply(lambda k: MAP_MODES[k])
    # Filter out invalid modes
    df = df[df.key != 'IGNORED']
    # Compute zone_key
    df['zone_key'] = df['perimetre'].apply(lambda k: MAP_ZONES[k])
    # Compute values
    df.value = df.value.replace('ND', np.nan).replace('-', np.nan).astype('float')
    # Storage works the other way around (RTE treats storage as production)
    df.loc[df.key.str.startswith('storage.'), 'value'] *= -1
    return df


def format_production_df(df, zone_key):
    # There can be multiple rows with the same key
    # (e.g. multiple things lumping into `unknown`)
    # so we need to group them and sum.
    df = (df[df.zone_key == zone_key]
            .reset_index()
            .groupby(['datetime', 'key'])
            # We use `min_count=1` to make sure at least one non-NaN
            # value is present to compute a sum.
            .sum(min_count=1)
            # We unstack `key` which creates a df where keys are columns
            .unstack('key')['value'])
    return [
        {
            'zoneKey': zone_key,
            'datetime': ts.to_pydatetime(),
            'production': (
                row
                    .filter(like='production.')
                    .rename(lambda c: c.replace('production.', ''))
                    .to_dict()
            ),
            'storage': (
                row
                    .filter(like='storage.')
                    .rename(lambda c: c.replace('storage.', ''))
                    .to_dict()
            ),
            'source': 'rte-france.com/eco2mix'
        }
        for (ts, row) in df.iterrows()
    ]

@refetch_frequency(timedelta(days=1))
def fetch_production(zone_key, session=None, target_datetime=None,
                     logger: Logger = getLogger(__name__)):

    datapoints = [
        validate(d, logger, required=VALIDATIONS.get(zone_key, []))
        for d in format_production_df(
            df=parse_production_to_df(
                query_production(session, target_datetime)),
            zone_key=zone_key)
    ]

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
