import arrow
import datetime
import json
import logging
import requests

import pandas as pd
import numpy as np

ZONE_KEY_TO_REGION = {
    'AUS-NSW': 'nsw1',
    'AUS-QLD': 'qld1',
    'AUS-SA': 'sa1',
    'AUS-TAS': 'tas1',
    'AUS-VIC': 'vic1',
}
SOURCE = 'opennem.org'


def dataset_to_df(dataset):
    series = dataset['history']
    interval = series['interval']
    dt_i = datetime.datetime.strptime(series['start'], '%Y-%m-%dT%H:%M+1000')
    dt_f = datetime.datetime.strptime(series['last'], '%Y-%m-%dT%H:%M+1000')
    _type = dataset['type']
    _id = dataset['id']

    if _type != 'power':
        name = _type.upper()
    else:
        name = _id.split(".")[-2].upper()

    # Turn into minutes
    if interval[-1] == "m":
        interval += "in"

    index = pd.date_range(start=dt_i, end=dt_f, freq=interval)[1:]
    df = pd.DataFrame(index=index, data=series['data'], columns=[name])
    return df


def fetch_main_df(zone_key=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    region = ZONE_KEY_TO_REGION[zone_key]
    # Fetches the last week of data
    r = (session or requests).get(f'http://data.opennem.org.au/power/{region}.json')
    r.raise_for_status()
    datasets = r.json()
    df = pd.concat([dataset_to_df(x) for x in datasets], axis=1)
    return df


def sum_vector(pd_series, keys, transform=lambda x: x):
    # Only consider keys that are in the pd_series
    filtered_keys = [k for k in keys if k in pd_series.index]
    if filtered_keys and all([not np.isnan(pd_series[k]) for k in filtered_keys]):
        return pd_series[filtered_keys].apply(transform).sum()
    else:
        return None


def fetch_production(zone_key=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    df = fetch_main_df(zone_key, session, target_datetime, logger)
    # List of fuels
    # fuel_tech = ["BIOMASS","BLACK_COAL", "BROWN_COAL", "DISTILLATE", "GAS_CCGT",
    #   "GAS_OCGT", "GAS_RECIP", "GAS_STEAM", "HYDRO", "PUMPS", "SOLAR", "WIND", "BATTERY"]

    # Make sure charging is counted positively
    # and discharging negetively
    if 'BATTERY_DISCHARGING' in df.columns:
        df['BATTERY_DISCHARGING'] = df['BATTERY_DISCHARGING'] * -1

    return [{
        'datetime': datetime.to_pydatetime(),
        'production': {  # Unit is MW
            'coal': sum_vector(row, ['BLACK_COAL', 'BROWN_COAL']),
            'gas': sum_vector(row, ['GAS_CCGT', 'GAS_OCGT', 'GAS_RECIP', 'GAS_STEAM']),
            'oil': sum_vector(row, ['DISTILLATE']),
            'hydro': sum_vector(row, ['HYDRO']),
            'wind': sum_vector(row, ['WIND']),
            # We here assume all rooftop solar is fed to the grid
            # This assumption should be checked and we should here only report
            # grid-level generation
            'solar': sum_vector(row, ['SOLAR', 'ROOFTOP_SOLAR']),
        },
        'storage': {
            # opennem reports charging as negative, we here should report as positive
            # Note: we made the sign switch before, so we can just sum them up
            'battery': sum_vector(row, ['BATTERY_DISCHARGING', 'BATTERY_CHARGING']),
            # opennem reports pumping as positive, we here should report as positive
            'hydro': sum_vector(row, ['PUMPS']),
        },
        'source': SOURCE,
        'zoneKey': zone_key,
    } for datetime, row in df.iterrows()]


def fetch_price(zone_key=None, session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    df = fetch_main_df(zone_key, session, target_datetime, logger)
    return [{
        'datetime': datetime.to_pydatetime(),
        'price': sum_vector(row, ['PRICE']),  # currency / MWh
        'currency': 'AUD',
        'source': SOURCE,
        'zoneKey': zone_key,
    } for datetime, row in df.iterrows()]


if __name__ == '__main__':
    """Main method, never used by the electricityMap backend, but handy for testing."""
    # print(fetch_price('AUS-SA'))
    print(fetch_production('AUS-SA'))

    # TODO: Interconnectors?
