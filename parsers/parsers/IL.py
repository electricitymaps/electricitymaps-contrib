#!/usr/bin/env python3
# coding=utf-8

# This parser returns Israel's electricity system load (assumed to be equal to electricity production)
# Source: Israel Electric Corporation
# URL: https://www.iec.co.il/en/pages/default.aspx
# Shares of Electricity production in 2018: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/data-and-statistics?country=ISRAEL&fuel=Electricity%20and%20heat&indicator=Electricity%20generation%20by%20source)


import arrow
import requests
import re
from bs4 import BeautifulSoup


def fetch_production(zone_key='IL', session=None, logger=None):
    first = requests.get('https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx')
    first.cookies
    second = requests.get('https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx', cookies=first.cookies)

    soup = BeautifulSoup(second.content, 'lxml')

    span = soup.find("span", attrs={"class": "statusVal"})
    value = re.findall("\d+", span.text.replace(",", ""))
    load = int(value[0])
    production = {}
    production['unknown'] = load
    
    datapoint = {
        'zoneKey': zone_key,
        'datetime': arrow.now('Asia/Jerusalem').datetime,
        'production': production,
        'source': 'iec.co.il'
    }

    return datapoint


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    
    print('fetch_production() ->')
    print(fetch_production())
