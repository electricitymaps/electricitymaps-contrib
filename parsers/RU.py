#!/usr/bin/python3
# -*- coding: utf-8 -*-

import arrow
from bs4 import BeautifulSoup
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

exchange_ids = {'CN->RU-AS': "764",
                'MN->RU': "276",
                'KZ->RU': "785",
                'GE->RU': "752",
                'AZ->RU': "598",
                'BY->RU': "321",
                'RU->UA': "880"}

# Each exchange is contained in a div tag with a "data-id" attribute that is unique.


tz = 'Europe/Moscow'


def fetch_production(country_code='RU', session=None, target_datetime=None, logger=None):
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
    url = 'http://br.so-ups.ru/Public/Export/Csv/PowerGen.aspx?&startDate={date}&endDate={date}&territoriesIds=-1:&notCheckedColumnsNames='.format(
        date=today)

    response = r.get(url)
    content = response.text

    # Prepare content and load as csv into Dataset
    dataset = tablib.Dataset()
    dataset.csv = content.replace('\xce\xdd\xd1', ' ').replace(',', '.').replace(';', ',')

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
                row['production'][production_type] = row['production'].get(production_type,
                                                                           0.0) + gen_value
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


def fetch_exchange(country_code1, country_code2, session=None, target_datetime=None, logger=None):
    """Requests the last known power exchange (in MW) between two zones
    Arguments:
    country_code1           -- the first country code
    country_code2           -- the second country code; order of the two codes in params doesn't matter
    session (optional)      -- request session passed in order to re-use an existing session
    Return:
    A list of dictionaries in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    where net flow is from DK into NO
    """

    exchanges_url = 'http://br.so-ups.ru/Public/MainPage.aspx'
    s = session or requests.Session()
    req = s.get(exchanges_url)
    soup = BeautifulSoup(req.content, 'html.parser')

    sortedcodes = '->'.join(sorted([country_code1, country_code2]))

    if sortedcodes not in exchange_ids.keys():
        raise NotImplementedError('This exchange pair is not implemented.')

    current_dt = arrow.now('Europe/Moscow').datetime

    data_id = exchange_ids[sortedcodes]
    find_id = soup.find("div", {"data-id": data_id})

    # Due to the html formatting being different for Belarus & Ukraine this check is required.
    if sortedcodes in ['BY->RU', 'RU->UA']:
        flow_val = find_id.find("div", {"class": "flow-value"})
        flow_dir = find_id.find_next("div")
    else:
        flow_val = find_id.find("td", {"class": "flow-value"})
        flow_dir = find_id.find("div", {"class": "relative-box"}).find_next("div")

    parsed_val = flow_val.get_text().strip()
    flow = float(parsed_val.split(' ')[0])

    # To determine the flow direction we use the class attribute of the following style of div tag that is nearby.
    # <div class="c-flow-arrow west-flow-arrow arrow-forward">
    check_flow = flow_dir["class"]

    if sortedcodes == 'RU->UA':
        # Order of zones requires reversal for Ukraine exchange.
        if check_flow[-1] == "arrow-backward":
            flow = flow * -1
        elif check_flow[-1] == "arrow-forward":
            pass
        else:
            raise ValueError(
                'The direction of the {} exchange cannot be determined.'.format(sortedcodes))
    elif check_flow[-1] == "arrow-forward":
        flow = flow * -1
    elif check_flow[-1] == "arrow-backward":
        pass
    else:
        raise ValueError(
            'The direction of the {} exchange cannot be determined.'.format(sortedcodes))

    exchange = {
        'sortedCountryCodes': sortedcodes,
        'datetime': current_dt,
        'netFlow': flow,
        'source': 'so-ups.ru'
    }

    return exchange


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(CN, RU-AS) ->')
    print(fetch_exchange('CN', 'RU-AS'))
    print('fetch_exchange(MN, RU) ->')
    print(fetch_exchange('MN', 'RU'))
    print('fetch_exchange(KZ, RU) ->')
    print(fetch_exchange('KZ', 'RU'))
    print('fetch_exchange(GE, RU) ->')
    print(fetch_exchange('GE', 'RU'))
    print('fetch_exchange(AZ, RU) ->')
    print(fetch_exchange('AZ', 'RU'))
    print('fetch_exchange(BY, RU) ->')
    print(fetch_exchange('BY', 'RU'))
    print('fetch_exchange(RU, UA) ->')
    print(fetch_exchange('RU', 'UA'))
