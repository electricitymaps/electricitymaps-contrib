#!/usr/bin/env python3

import arrow
from . import ENTSOE
import logging
import pandas as pd
import requests


def fetch_production(zone_key='NL', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    if target_datetime:
        now = arrow.get(target_datetime, 'Europe/Paris')
    else:
        now = arrow.now(tz='Europe/Paris')

    r = session or requests.session()

    consumptions = ENTSOE.fetch_consumption(zone_key=zone_key,
                                            session=r,
                                            target_datetime=now,
                                            logger=logger)
    for c in consumptions:
        del c['source']
    df_consumptions = pd.DataFrame.from_dict(consumptions).set_index('datetime')

    # NL has exchanges with BE, DE, NO, GB
    exchanges = []
    for exchange_key in ['BE', 'DE', 'NO', 'GB']:
        zone_1, zone_2 = sorted([exchange_key, zone_key])
        exchange = ENTSOE.fetch_exchange(zone_key1=zone_1,
                                         zone_key2=zone_2,
                                         session=r,
                                         target_datetime=now,
                                         logger=logger)
        for e in exchange:
            e['NL_import'] = e['netFlow'] if zone_2 == 'NL' else -1 * e['netFlow']
            del e['source']
        exchanges.extend(exchange or [])
    df_exchanges = pd.DataFrame.from_dict(exchanges).set_index('datetime')
    # Sum all exchanges to NL imports
    df_exchanges = df_exchanges.groupby('datetime').sum()

    # Fill missing values by propagating the value forward
    df_consumptions_with_exchanges = df_consumptions.join(df_exchanges).fillna(
        method='ffill')

    # Load = Generation + netImports
    # => Generation = Load - netImports
    df_total_generations = df_consumptions_with_exchanges['consumption'] - \
        df_consumptions_with_exchanges['NL_import']

    # Fetch all production
    productions = ENTSOE.fetch_production(zone_key=zone_key, session=r,
                                          target_datetime=now, logger=logger)

    # Flatten production dictionaries (we ignore storage)
    for p in productions:
        # We here assume 0 storage
        # Set coal, gas, nuclear to unknown
        p['production']['coal'] = None
        p['production']['gas'] = None
        p['production']['nuclear'] = None
        p['production']['unknown'] = 0
        Z = sum([x or 0 for x in p['production'].values()])
        p['production']['unknown'] = df_total_generations[p['datetime']] - Z

    return productions


if __name__ == '__main__':
    print(fetch_production())
