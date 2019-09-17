#!/usr/bin/env python3

"""Parser for power production in Croatia"""

import arrow
import requests
import logging
import pandas as pd

url = "https://www.hops.hr/Home/PowerExchange"

def fetch_production(zone_key='HR', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):

    r = session or requests.session()
    response = r.get(url)
    obj = response.json()

    # We assume the timezone of the time returned is local time and convert to UTC
    date_time = arrow.get(obj['updateTime']).replace(tzinfo='Europe/Belgrade').to('utc')

    # The json returned contains a list of values
    # 0 - 9 are individual exchanges with neighbouring countries
    # 10 - 13 are cumulative exchanges with neigbouring countries
    # 14 grid frequency
    # 15 total load of Croatia
    # 16 'Ukupna proizvodnja'  total generation
    # 17 'Proizvodnja VE'      wind generation
    df = pd.DataFrame.from_dict(obj['resources']).set_index('sourceName')

    # Get the wind power generation
    wind = df['value'].loc['Proizvodnja VE']

    # Get the total power generation and substract wind power
    unknown = df['value'].loc['Ukupna proizvodnja'] - wind

    return  [{
                'zoneKey': 'HR',
                'datetime': date_time.datetime,
                'production': {
                    'wind' : wind,
                    'unknown' : unknown
                },
                'source': 'hops.hr'
            }]

if __name__ == '__main__':
    print('fetch_oroduction(HR)->')
    print(fetch_production('HR'))
