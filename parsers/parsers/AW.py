#!/usr/bin/env python3

import arrow
import requests
import datetime


def fetch_production(zone_key='AW', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'https://www.webaruba.com/renewable-energy-dashboard/app/rest/results.json'
    # User agent is mandatory or services answers 404
    headers = {'user-agent': 'electricitymap.org'}
    response = r.get(url, headers=headers)
    aruba_json = response.json()
    top_data = aruba_json['dashboard_top_data']

    # Values currenlty used from service
    fossil = top_data['Fossil']
    wind = top_data['Wind']
    solar = top_data['TotalSolar']

    # We're using Fossil data to get timestamp in correct time zone
    local_date_time = datetime.datetime.strptime(fossil['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
    zone_date_time = arrow.Arrow.fromdatetime(local_date_time, 'America/Aruba')

    data = {
        'zoneKey': zone_key,
        'datetime': zone_date_time.datetime,
        'production': {
            'oil': float(fossil['value']),
            'wind': float(wind['value']),
            'solar': float(solar['value']),
        },
        'storage': {},
        'source': 'webaruba.com',
    }

    return data


if __name__ == '__main__':
    print(fetch_production())
