#!/usr/bin/python3
## -*- coding: utf-8 -*-

import arrow
import dateutil
import requests
import tablib

MAP_GENERATION = {
    'P_AES': 'nuclear',
    'P_GES': 'hydro',
    'P_GRES': 'unknown',
    'P_TES': 'unknown',
    'P_BS': 'unknown'
}

tz = 'Europe/Moscow'


def fetch_production(country_code='RU', session=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'countryCode': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """

    r = session or requests.session()
    today = arrow.now(tz=tz).format('DD.MM.YYYY')
    url = 'http://br.so-ups.ru/Public/Export/Csv/PowerGen.aspx?&startDate={date}&endDate={date}&territoriesIds=-1:&notCheckedColumnsNames='.format(date=today)

    response = r.get(url)
    content = response.text

    # Prepare content and load as csv into Dataset
    dataset = tablib.Dataset()
    dataset.csv = content.replace('\xce\xdd\xd1', ' ').replace(',','.').replace(';',',')

    data = []
    for datapoint in dataset.dict:
        row = {
            'countryCode': country_code,
            'production': {},
            'storage': {},
            'source': 'so-ups.ru'
        }

        # Production
        for k, production_type in MAP_GENERATION.items():
            if k in datapoint:
                gen_value = float(datapoint[k])
                row['production'][production_type] = row['production'].get(production_type, 0.0) + gen_value
            else:
                row['production']['unknown'] = row['production'].get('unknown', 0.0) + gen_value

        # Date
        hour = '%02d' % int(datapoint['INTERVAL'])
        date = arrow.get('%s %s' % (today, hour), 'DD.MM.YYYY HH')
        row['datetime'] = date.replace(tzinfo=dateutil.tz.gettz(tz)).datetime

        current_dt = arrow.now('Europe/Moscow').datetime

        # Drop datapoints in the future
        if row['datetime'] > current_dt:
            continue

        # Default values
        row['production']['solar'] = None
        row['production']['biomass'] = None
        row['production']['geothermal'] = None

        data.append(row)


    return data

if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
