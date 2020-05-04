#!/usr/bin/env python3
# coding=utf-8

# This parser returns Kuwait's electricity system load (assumed to be equal to electricity production)
# Source: Ministry of Electricity and Water / State of Kuwait
# URL: https://www.mew.gov.kw/en/
# Scroll down to see the system load gauge
# Shares of Electricity production in 2017: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/statistics/?country=KUWAIT&indicator=ElecGenByFuel)

import arrow
import requests
import re

def fetch_consumption(zone_key='KW', session=None, logger=None):
    r = session or requests.session()
    url = 'https://www.mew.gov.kw/en'
    response = r.get(url)
    load = re.findall(r"\((\d{4,5})\)", response.text)
    load = int(load[0])
    consumption = load
    
    datapoint = {
        'zoneKey': zone_key,
        'datetime': arrow.now('Asia/Kuwait').datetime,
        'consumption': consumption,
        'source': 'mew.gov.kw'
    }

    return datapoint

if __name__ == '__main__':
    """Main method, never used by the electricityMap backend, but handy for testing."""
    
    print('fetch_consumption() ->')
    print(fetch_consumption())
