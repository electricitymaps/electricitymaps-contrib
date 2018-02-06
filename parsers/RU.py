#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

import arrow
import dateutil
import requests
import tablib

MAP_GENERATION = {
    'P_AES': 'nuclear',
    'P_GES': 'hydro',
}

FOSIL_TYPES = [
    'P_GRES', # https://en.wikipedia.org/wiki/Thermal_power_stations_in_Russia_and_Soviet_Union
    'P_TES', # https://en.wikipedia.org/wiki/Thermal_power_station
    'P_BS', # Could be fosil...
]

# Aprox fosil shares
FOSIL_SHARES = {
    'gas': 0.71,
    'coal': 0.28,
    'oil': 0.01,
}

tz = 'Europe/Moscow'

def fetch_production(country_code='RU', session=None):
    r = session or requests.session()

    today = arrow.now(tz=tz).format('DD.MM.YYYY')
    url = 'http://br.so-ups.ru/Public/Export/Csv/PowerGen.aspx?&startDate={date}&endDate={date}&territoriesIds=-1:&notCheckedColumnsNames='.format(date=today)

    response = r.get(url)
    content = response.content

    # Prepare content and load as csv into Dataset
    dataset = tablib.Dataset()
    dataset.csv = content.replace('\xce\xdd\xd1', ' ').replace(',','.').replace(';',',')

    data = []
    for serie in dataset.dict:
        row = {
            'countryCode': country_code,
            'production': {},
            'storage': {},
            'source': 'ua.energy'
        }

        # Production
        for k, production_type in MAP_GENERATION.items():
            if k in serie:
                row['production'][production_type] = int(float(serie[k]))
            else:
                row['production'][production_type] = 0.0

        # Calculate approximate value of each fosil type
        fosil_production = 0
        for fosil_type in FOSIL_TYPES:
            if fosil_type in serie:
                fosil_production += int(float(serie[fosil_type]))

        for fosil_type, percent in FOSIL_SHARES.items():
            row['production'][fosil_type] = int(fosil_production * percent)

        # Date
        hour = '%02d' % int(serie['INTERVAL'])
        date = arrow.get('%s %s' % (today, hour), 'DD.MM.YYYY HH')
        row['datetime'] = date.replace(tzinfo=dateutil.tz.gettz(tz)).datetime

        # Default values
        row['production']['solar'] = 0
        row['production']['biomass'] = 0
        row['production']['geothermal'] = 0

        data.append(row)


    return data

if __name__ == '__main__':
    print(fetch_production())
