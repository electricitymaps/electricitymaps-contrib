#!/usr/bin/env python3

import arrow
import pprint
import math

from . import statnett
from . import ENTSOE
from . import DK
import logging
import pandas as pd
import requests


def fetch_production(zone_key='NL', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__), energieopwek_nl=True):
    if target_datetime is None:
        target_datetime = arrow.utcnow()

    r = session or requests.session()

    consumptions = ENTSOE.fetch_consumption(zone_key=zone_key,
                                            session=r,
                                            target_datetime=target_datetime,
                                            logger=logger)
    if not consumptions:
        return
    for c in consumptions:
        del c['source']
    df_consumptions = pd.DataFrame.from_dict(consumptions).set_index(
        'datetime')

    # NL has exchanges with BE, DE, NO, GB, DK-DK1
    exchanges = []
    for exchange_key in ['BE', 'DE', 'GB']:
        zone_1, zone_2 = sorted([exchange_key, zone_key])
        exchange = ENTSOE.fetch_exchange(zone_key1=zone_1,
                                         zone_key2=zone_2,
                                         session=r,
                                         target_datetime=target_datetime,
                                         logger=logger)
        if not exchange:
            return
        exchanges.extend(exchange or [])

    # add NO data, fetch once for every hour
    # This introduces an error, because it doesn't use the average power flow
    # during the hour, but rather only the value during the first minute of the
    # hour!
    zone_1, zone_2 = sorted(['NO', zone_key])
    exchange_NO = [statnett.fetch_exchange(zone_key1=zone_1, zone_key2=zone_2,
                                        session=r, target_datetime=dt.datetime,
                                        logger=logger)
                for dt in arrow.Arrow.range(
            'hour',
            arrow.get(min([e['datetime']
                                for e in exchanges])).replace(minute=0),
            arrow.get(max([e['datetime']
                           for e in exchanges])).replace(minute=0))]
    exchanges.extend(exchange_NO)

    # add DK1 data
    zone_1, zone_2 = sorted(['DK-DK1', zone_key])
    df_dk = pd.DataFrame(DK.fetch_exchange(zone_key1=zone_1, zone_key2=zone_2,
                                        session=r, target_datetime=target_datetime,
                                        logger=logger))

    # Because other exchanges and consumption data is only available per hour
    # we floor the timpstamp to hour and group by hour with averaging of netFlow
    df_dk['datetime'] = df_dk['datetime'].dt.floor('H')
    exchange_DK = df_dk.groupby(['datetime']).aggregate({'netFlow' : 'mean', 
        'sortedZoneKeys': 'max', 'source' : 'max'}).reset_index()

    # because averaging with high precision numbers leads to rounding errors
    exchange_DK = exchange_DK.round({'netFlow': 3})

    exchanges.extend(exchange_DK.to_dict(orient='records'))

    # We want to know the net-imports into NL, so if NL is in zone_1 we need
    # to flip the direction of the flow. E.g. 100MW for NL->DE means 100MW
    # export to DE and needs to become -100MW for import to NL.
    for e in exchanges:
        e['NL_import'] = e['netFlow'] if zone_1 == 'NL' else -1 * e['netFlow']
        del e['source']

    df_exchanges = pd.DataFrame.from_dict(exchanges).set_index('datetime')
    # Sum all exchanges to NL imports
    df_exchanges = df_exchanges.groupby('datetime').sum()

    # Fill missing values by propagating the value forward
    df_consumptions_with_exchanges = df_consumptions.join(df_exchanges).fillna(
        method='ffill', limit=3)  # Limit to 3 x 15min

    # Load = Generation + netImports
    # => Generation = Load - netImports
    df_total_generations = (df_consumptions_with_exchanges['consumption']
                            - df_consumptions_with_exchanges['NL_import'])

    # Fetch all production
    # The energieopwek_nl parser is backwards compatible with ENTSOE parser.
    # Because of data quality issues we switch to using energieopwek, but if
    # data quality of ENTSOE improves we can switch back to using a single
    # source.
    if energieopwek_nl:
        productions = fetch_production_energieopwek_nl(session=r,
                            target_datetime=target_datetime, logger=logger)
    else:
        productions = ENTSOE.fetch_production(zone_key=zone_key, session=r,
                            target_datetime=target_datetime, logger=logger)
    if not productions:
        return

    # Flatten production dictionaries (we ignore storage)
    for p in productions:
        # We here assume 0 storage
        p['production']['coal'] = None
        p['production']['gas'] = None
        p['production']['biomass'] = None

        p['production']['unknown'] = 0
        Z = sum([x or 0 for x in p['production'].values()])
        # Only calculate the difference if the datetime exists
        if p['datetime'] in df_total_generations:
            p['production']['unknown'] = round((df_total_generations[p['datetime']]
                                          - Z), 3)

    # Filter invalid
    return [p for p in productions if p['production']['unknown'] > 0]


def fetch_production_energieopwek_nl(session=None, target_datetime=None,
                                     logger=logging.getLogger(__name__)):
    if target_datetime is None:
        target_datetime = arrow.utcnow()

    r = session or requests.session()

    # The API returns values per day from local time midnight until the last
    # round 10 minutes if the requested date is today or for the entire day if
    # it's in the past. 'sid' can be anything.
    date = target_datetime.format('YYYY-MM-DD')
    url = 'http://energieopwek.nl/jsonData.php?sid=2ecde3&Day=&Day=%s' % date
    response = r.get(url)
    obj = response.json()
    production_input = obj['TenMin']['Country']

    # extract the power values in kW from the different production types
    # we only need column 0; 1 and 3 contain energy sum values
    df_solar =    pd.DataFrame(production_input['Solar'])       .drop(['1','3'], axis=1).astype(int).rename(columns={"0" : "Solar"})
    df_offshore = pd.DataFrame(production_input['WindOffshore']).drop(['1','3'], axis=1).astype(int)
    df_onshore =  pd.DataFrame(production_input['Wind'])        .drop(['1','3'], axis=1).astype(int)

    # We don't differentiate between onshore and offshore wind so we sum them toghether an build a
    # single data frame with named columns
    df_wind = df_onshore.add(df_offshore).rename(columns={"0": "wind"})
    df = pd.concat([df_solar, df_wind], axis=1)

    # resample from 10min resolution to 15min resolution
    # we duplicate every row and then group them per 3 and take the mean
    df = pd.concat([df]*2).sort_index(axis=0).reset_index(drop=True).groupby(by=lambda x : round(x/3)).mean()

    # Convert kW to MW with kW resolution
    df = df.apply(lambda x: round(x / 1000, 3))

    # Rename columns
    df = df.rename(columns={"Solar": "solar"})

    output = []
    base_time = arrow.get(target_datetime.date(), 'Europe/Paris').to('utc')

    for i, prod in enumerate(df.to_dict(orient='records')):
        output.append(
            {
                'zoneKey': 'NL',
                'datetime': base_time.shift(minutes=i*15).datetime,
                'production': prod,
                'source': 'energieopwek.nl, entsoe.eu'
            }
        )
    return output

if __name__ == '__main__':
    print(fetch_production())
