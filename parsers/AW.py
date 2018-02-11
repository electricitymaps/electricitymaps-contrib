#!/usr/bin/env python3

import arrow
import requests
import datetime

def fetch_production(country_code='AW', session=None):
    r = session or requests.session()
    url = 'https://www.webaruba.com/renewable-energy-dashboard/app/rest/results.json'
    #User agent is mandatory or services answers 404
    headers = {'user-agent': 'electricitymap.org'}
    response = r.get(url, headers=headers)
    arubaJson = response.json();
    topData = arubaJson['dashboard_top_data']

    #Values currenlty used from service    
    fossil = topData['Fossil']
    wind = topData['Wind']
    solar = topData['TotalSolar']
    
    #We're using Fossil data to get timestamp in correct time zone
    localDateTime = datetime.datetime.strptime(fossil['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
    zoneDateTime = arrow.Arrow.fromdatetime(localDateTime, 'America/Aruba')
    
    data = {
        'countryCode': country_code,
        'datetime': zoneDateTime.datetime,
        'production': {
            'oil': fossil['value'],
            'wind': wind['value'],
            'solar': solar['value'],
        },
        'storage': {},
        'source': 'webaruba.com',
    }

    return data

if __name__ == '__main__':
    print(fetch_production())
