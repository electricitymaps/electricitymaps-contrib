#!/usr/bin/env python3
# coding=utf-8

# This parser returns Israel's electricity system load (assumed to be equal to electricity production)
# Source: Israel Electric Corporation
# URL: https://www.iec.co.il/en/pages/default.aspx
# Shares of Electricity production in 2018: 65.6% oil, 34.4% gas (source: IEA; https://www.iea.org/data-and-statistics?country=ISRAEL&fuel=Electricity%20and%20heat&indicator=Electricity%20generation%20by%20source)


import re

import arrow
import requests
from bs4 import BeautifulSoup

IEC_URL = "iec.co.il"
IEC_PRODUCTION = (
    "https://www.iec.co.il/_layouts/iec/applicationpages/lackmanagment.aspx"
)
PRICE = "50.66"  # Price is determined yearly

def flatten_list(_2d_list):
    flat_list = []
    # Iterate through the outer list
    for element in _2d_list:
        if type(element) is list:
            # If the element is of type list, iterate through the sublist
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list

# def fetch():
#     first = requests.get(IEC_PRODUCTION)
#     first.cookies
#     with requests.get(IEC_PRODUCTION, cookies=first.cookies) as second:
#         soup = BeautifulSoup(second.content, "lxml")

#         values:list = soup.find_all("span", class_='statusVal')
#         del values[1]

#         cleaned_list = []
#         for value in values:
#             value = re.findall("\d+", value.text.replace(",", ""))
#             cleaned_list.append(value)

#         cleaned_list = flatten_list(cleaned_list)

#         int_list = [int(item) for item in cleaned_list]
#     return int_list

def fetch_production(zone_key="IL", session=None, logger=None):
    first = requests.get(IEC_PRODUCTION)
    first.cookies
    with requests.get(IEC_PRODUCTION, cookies=first.cookies) as second:
        soup = BeautifulSoup(second.content, "lxml")

        values:list = soup.find_all("span", class_='statusVal')
        del values[1]

        cleaned_list = []
        for value in values:
            value = re.findall("\d+", value.text.replace(",", ""))
            cleaned_list.append(value)

        cleaned_list = flatten_list(cleaned_list)

        int_list = [int(item) for item in cleaned_list]

    data = {
        "zoneKey": zone_key,
        "datetime": arrow.now("Asia/Jerusalem").datetime,
        'production': {
            'biomass': 0.0,
            'coal':  0.0,
            'gas':  0.0,
            'oil': 0.0,
            'solar':  0.0,
            'wind':  0.0,
            'geothermal': 0.0,
            'unknown': int_list[0] + int_list[1]
            },
        "source": IEC_URL,
        "price": PRICE,
    }

    return data

# def fetch_consumption(zone_key='IL', session=None, target_datetime=None, logger=None):
#     int_list = fetch()

#     load = int_list[0]
#     consumption = {}
#     consumption['unknown'] = load

#     data = {
#         'zoneKey': zone_key,
#         'datetime': arrow.now("Asia/Jerusalem").datetime,
#         'consumption': consumption,
#         'source': IEC_URL
#     }

#     return data

if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
