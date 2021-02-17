#!/usr/bin/env python3

import arrow

from . import ENTSOE
import logging
import requests


def fetch_swiss_exchanges(session, target_datetime, logger):
    """Returns the total exchanges of Switzerland with its neighboring countries."""
    swiss_transmissions = {}
    for exchange_key in ['AT', 'DE', 'IT', 'FR']:
        exchanges = ENTSOE.fetch_exchange(zone_key1='CH',
                                          zone_key2=exchange_key,
                                          session=session,
                                          target_datetime=target_datetime,
                                          logger=logger)
        if not exchanges:
            continue

        for exchange in exchanges:
            datetime = exchange['datetime']
            if datetime not in swiss_transmissions:
                swiss_transmissions[datetime] = exchange['netFlow']
            else:
                swiss_transmissions[datetime] += exchange['netFlow']

    return swiss_transmissions


def fetch_swiss_consumption(session, target_datetime, logger):
    """Returns the total consumption of Switzerland."""
    consumptions = ENTSOE.fetch_consumption(zone_key='CH',
                                            session=session,
                                            target_datetime=target_datetime,
                                            logger=logger)
    return {c['datetime']: c['consumption'] for c in consumptions}


def fetch_production(zone_key='CH', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    """
    Returns the total production by type for Switzerland.
    Currently the majority of the run-of-river production is missing.
    The difference between the sum of all production types and the total production is allocated as 'unknown'.
    The total production is calculated as sum of the consumption, storage and net imports.
    """
    now = arrow.get(target_datetime, 'Europe/Zurich') if target_datetime else arrow.now(tz='Europe/Zurich')
    r = session or requests.session()

    exchanges = fetch_swiss_exchanges(r, now, logger)
    consumptions = fetch_swiss_consumption(r, now, logger)
    productions = ENTSOE.fetch_production(zone_key=zone_key, session=r, target_datetime=now, logger=logger)

    if not productions:
        return

    for p in productions:
        dt = p['datetime']
        if dt not in exchanges or dt not in consumptions:
            continue
        known_production = sum([x or 0 for x in p['production'].values()])

        storage = sum([x or 0 for x in p['storage'].values()])
        total_production = consumptions[dt] + storage + exchanges[dt]
        unknown_production = total_production - known_production
        p['production']['unknown'] = unknown_production if unknown_production > 0 else 0

    return productions


if __name__ == '__main__':
    print(fetch_production())
