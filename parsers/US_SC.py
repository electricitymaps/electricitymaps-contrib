#!/usr/bin/env python3
"""Parser for South Carolina, USA.

Historical data only right now, via EIA. Generation comes from two sources:

South Carolina Electric & Gas Co, a division of SCANA, acquired by Dominion
Energy in Jan 2019.
https://www.scana.com/
https://en.wikipedia.org/wiki/SCANA

South Carolina Public Service Authority, aka Santee Cooper
http://www.santeecooper.com/
https://en.wikipedia.org/wiki/Santee_Cooper

https://github.com/tmrowco/electricitymap-contrib/issues/1674
"""
import logging

from . import EIA
from .ENTSOE import merge_production_outputs


def fetch_production(zone_key='US-SC', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    sc = fetch_unknown(zone_key='US-SC', session=session,
                       target_datetime=target_datetime, logger=logger)
    sceg = fetch_unknown(zone_key='US-SCEG', session=session,
                         target_datetime=target_datetime, logger=logger)
    return merge_production_outputs((sc, sceg), zone_key)


def fetch_unknown(zone_key='US-SC', session=None, target_datetime=None,
                  logger=logging.getLogger(__name__)):
    data = EIA.fetch_production(zone_key=zone_key, session=session,
                                target_datetime=target_datetime, logger=logger)
    for hour in data:
        hour.update({
            'production': {'unknown': hour.pop('value')},
            'storage': {},  # required by merge_production_outputs
        })

    return data


def main():
    """Main method, not used by the ElectricityMap backend, just for testing."""
    import pprint
    print('fetch_production() ->')
    print(pprint.pprint(fetch_production()))


if __name__ == '__main__':
    main()
