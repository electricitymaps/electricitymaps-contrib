import arrow
import datetime
import json
import logging
import requests

import pandas as pd
import numpy as np

ZONE_KEY_TO_REGION = {
    'AUS-NSW': 'NSW1',
    'AUS-QLD': 'QLD1',
    'AUS-SA': 'SA1',
    'AUS-TAS': 'TAS1',
    'AUS-VIC': 'VIC1',
    'AUS-WA': 'WEM',
}
EXCHANGE_MAPPING_DICTIONARY = {
    'AUS-NSW->AUS-QLD': {
        'region_id': 'NSW1->QLD1',
        'direction': 1,
    },
    'AUS-NSW->AUS-VIC': {
        'region_id': 'VIC1->NSW1',
        'direction': 1,
    },
    'AUS-SA->AUS-VIC': {
        'region_id': 'VIC1->SA1',
        'direction': -1,
    },
    'AUS-TAS->AUS-VIC': {
        'region_id': 'TAS1->VIC1',
        'direction': 1,
    },
}
OPENNEM_PRODUCTION_CATEGORIES = {
    'coal': ['COAL_BLACK', 'COAL_BROWN'],
    'gas': ['GAS_CCGT', 'GAS_OCGT', 'GAS_RECIP', 'GAS_STEAM'],
    'oil': ['DISTILLATE'],
    'hydro': ['HYDRO'],
    'wind': ['WIND'],
    'biomass': ['BIOENERGY_BIOGAS', 'BIOENERGY_BIOMASS'],
    'solar': ['SOLAR_UTILITY', 'SOLAR_ROOFTOP'],
}
OPENNEM_STORAGE_CATEGORIES = {
    # Storage
    'battery': ['BATTERY_DISCHARGING', 'BATTERY_CHARGING'],
    'hydro': ['PUMPS'],
}
SOURCE = 'opennem.org'


def dataset_to_df(dataset):
    series = dataset['history']
    interval = series['interval']
    dt_start = arrow.get(series['start']).datetime
    dt_end = arrow.get(series['last']).datetime
    data_type = dataset['data_type']
    _id = dataset.get('id')

    if data_type != 'power':
        name = data_type.upper()
    else:
        # When `power` is given, the multiple power sources will be given
        # we therefore set `name` to the power source
        name = _id.split(".")[-2].upper()

    # Turn into minutes
    if interval[-1] == "m":
        interval += "in"

    index = pd.date_range(start=dt_start, end=dt_end, freq=interval)
    assert len(index) == len(series['data'])
    df = pd.DataFrame(index=index, data=series['data'], columns=[name])
    return df


def fetch_main_df(data_type, zone_key=None, sorted_zone_keys=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    if target_datetime:
        # We will fetch one week in the past
        df_start = arrow.get(target_datetime).shift(days=-7).datetime
        y, w, d = df_start.isocalendar()
        iso_week = "{0}W{1:02d}".format(y, w)
        raise NotImplementedError()
        # url = f'http://data.opennem.org.au/power/history/5minute/{region}_{iso_week}.json'
    else:
        url = f'https://data.dev.opennem.org.au/v3/clients/em/latest.json'

    # Fetches the last week of data
    r = (session or requests).get(url)
    r.raise_for_status()
    datasets = r.json()['data']
    filtered_datasets = [
        ds for ds in datasets
        if ds['type'] == data_type and (
            (zone_key and ds.get('region') == ZONE_KEY_TO_REGION[zone_key])
            or (sorted_zone_keys and ds.get('id').split('.')[-2] == EXCHANGE_MAPPING_DICTIONARY['->'.join(sorted_zone_keys)]['region_id'])
        )
    ]
    df = pd.concat([dataset_to_df(ds) for ds in filtered_datasets], axis=1)
    if data_type == 'power' and zone_key:
        # SOLAR_ROOFTOP is only given at 30 min interval, so let's interpolate it
        df['SOLAR_ROOFTOP'] = df['SOLAR_ROOFTOP'].interpolate(limit=5)
        # Parse capacity data
        capacities = dict([
            (obj['id'].split('.')[-2].upper(), obj.get('x_capacity_at_present'))
            for obj in filtered_datasets if obj['region'] == ZONE_KEY_TO_REGION[zone_key]
        ])
        return df, pd.Series(capacities)
    else:
        return df


def sum_vector(pd_series, keys, transform=lambda x: x):
    # Only consider keys that are in the pd_series
    filtered_keys = [k for k in keys if k in pd_series.index]
    # Require all present keys to be non-null
    if filtered_keys and pd_series[filtered_keys].notnull().all():
        return pd_series[filtered_keys].apply(transform).sum()
    else:
        return None


def fetch_production(zone_key=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    df, capacities = fetch_main_df('power', zone_key=zone_key, session=session, target_datetime=target_datetime, logger=logger)
    # Drop interconnectors
    df = df.drop([x for x in df.columns if '->' in x], axis=1)

    # Make sure charging is counted positively
    # and discharging negetively
    if 'BATTERY_DISCHARGING' in df.columns:
        df['BATTERY_DISCHARGING'] = df['BATTERY_DISCHARGING'] * -1

    objs = [{
        'datetime': arrow.get(dt.to_pydatetime()).datetime,
        'production': {  # Unit is MW
            'coal': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['coal']),
            'gas': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['gas']),
            'oil': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['oil']),
            'hydro': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['hydro']),
            'wind': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['wind']),
            'biomass': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['biomass']),
            # We here assume all rooftop solar is fed to the grid
            # This assumption should be checked and we should here only report
            # grid-level generation
            'solar': sum_vector(row, OPENNEM_PRODUCTION_CATEGORIES['solar']),
        },
        'storage': {
            # opennem reports charging as negative, we here should report as positive
            # Note: we made the sign switch before, so we can just sum them up
            'battery': sum_vector(row, OPENNEM_STORAGE_CATEGORIES['battery']),
            # opennem reports pumping as positive, we here should report as positive
            'hydro': sum_vector(row, OPENNEM_STORAGE_CATEGORIES['hydro']),
        },
        'capacity': {
            'coal': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['coal']),
            'gas': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['gas']),
            'oil': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['oil']),
            'hydro': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['hydro']),
            'wind': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['wind']),
            'biomass': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['biomass']),
            'solar': sum_vector(capacities, OPENNEM_PRODUCTION_CATEGORIES['solar']),
        },
        'source': SOURCE,
        'zoneKey': zone_key,
    } for dt, row in df.iterrows()]

    # Validation
    for obj in objs:
        for k, v in obj['production'].items():
            if v is None:
                continue
            if v < 0 and v > -50:
                # Set small negative values to 0
                logger.warning(f'Setting small value of {k} ({v}) to 0.',
                               extra={'key': zone_key})
                obj['production'][k] = 0

    return objs


def fetch_price(zone_key=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    df = fetch_main_df('price', zone_key=zone_key, session=session, target_datetime=target_datetime, logger=logger)
    df = df.loc[~df['PRICE'].isna()]  # Only keep prices that are defined
    return [{
        'datetime': arrow.get(dt.to_pydatetime()).datetime,
        'price': sum_vector(row, ['PRICE']),  # currency / MWh
        'currency': 'AUD',
        'source': SOURCE,
        'zoneKey': zone_key,
    } for dt, row in df.iterrows()]


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    sorted_zone_keys = sorted([zone_key1, zone_key2])
    key = '->'.join(sorted_zone_keys)
    df = fetch_main_df('power', sorted_zone_keys=sorted_zone_keys, session=session, target_datetime=target_datetime, logger=logger)
    direction = EXCHANGE_MAPPING_DICTIONARY[key]['direction']

    # Take the first column (there's only one)
    series = df.iloc[:, 0]

    return [{
        'datetime': arrow.get(dt.to_pydatetime()).datetime,
        'netFlow': value * direction,
        'source': SOURCE,
        'sortedZoneKeys': key,
    } for dt, value in series.iteritems()]


if __name__ == '__main__':
    """Main method, never used by the electricityMap backend, but handy for testing."""
    # print(fetch_price('AUS-SA'))
    print(fetch_production('AUS-WA'))
    # print(fetch_production('AUS-SA', target_datetime=arrow.get('2020-01-01T00:00:00Z').datetime))
