#!/usr/bin/env python3
import arrow
import requests
import pandas
import dateutil


def fetch_production(zone_key='TW', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    url = 'http://data.taipower.com.tw/opendata01/apply/file/d006001/001.txt'
    response = requests.get(url)
    data = response.json()

    dumpDate = data['']
    prodData = data['aaData']

    tz = 'Asia/Taipei'
    dumpDate = arrow.get(dumpDate, 'YYYY-MM-DD HH:mm').replace(tzinfo=dateutil.tz.gettz(tz))

    objData = pandas.DataFrame(prodData)

    objData.columns = ['fueltype', 'name', 'capacity', 'output', 'percentage',
                       'additional']

    objData['fueltype'] = objData.fueltype.str.split('(').str[1]
    objData['fueltype'] = objData.fueltype.str.split(')').str[0]
    objData.drop('additional', axis=1, inplace=True)
    objData.drop('percentage', axis=1, inplace=True)

    objData = objData.convert_objects(convert_numeric=True)
    production = pandas.DataFrame(objData.groupby('fueltype').sum())
    production.columns = ['capacity', 'output']

    coal_capacity = production.ix['Coal'].capacity + production.ix['IPP-Coal'].capacity
    gas_capacity = production.ix['LNG'].capacity + production.ix['IPP-LNG'].capacity
    oil_capacity = production.ix['Oil'].capacity + production.ix['Diesel'].capacity

    coal_production = production.ix['Coal'].output + production.ix['IPP-Coal'].output
    gas_production = production.ix['LNG'].output + production.ix['IPP-LNG'].output
    oil_production = production.ix['Oil'].output + production.ix['Diesel'].output

    # For storage, note that load will be negative, and generation positive.
    # We require the opposite

    returndata = {
        'zoneKey': zone_key,
        'datetime': dumpDate.datetime,
        'production': {
            'coal': coal_production,
            'gas': gas_production,
            'oil': oil_production,
            'hydro': production.ix['Hydro'].output,
            'nuclear': production.ix['Nuclear'].output,
            'solar': production.ix['Solar'].output,
            'wind': production.ix['Wind'].output,
            'unknown': production.ix['Co-Gen'].output
        },
        'capacity': {
            'coal': coal_capacity,
            'gas': gas_capacity,
            'oil': oil_capacity,
            'hydro': production.ix['Hydro'].capacity,
            'nuclear': production.ix['Nuclear'].capacity,
            'solar': production.ix['Solar'].capacity,
            'wind': production.ix['Wind'].capacity,
            'unknown': production.ix['Co-Gen'].capacity
        },
        'storage': {
            'hydro': -1 * production.ix['Pumping Load'].output - production.ix['Pumping Gen'].output
        },
        'source': 'taipower.com.tw'
    }

    return returndata


if __name__ == '__main__':
    print(fetch_production())
