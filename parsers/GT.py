#!/usr/bin/env python3
# coding=utf-8

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# The pandas library is used to manipulate real time data
import pandas as pd

tz_gt = 'America/Guatemala'

MAP_GENERATION = {
    'coal': 'Turbina de Vapor',
    'gas': 'Turbina de Gas',
    'hydro': u'Hidroeléctrica',
    'oil': 'Motor Reciprocante',
    'solar': 'Fotovoltaica',
    'wind': u'Eólico',
    'geothermal': u'Geotérmica',
}


def fetch_hourly_production(zone_key, obj, hour, date):

    # output frame
    data = {
        'zoneKey': zone_key,
        'production': {},
        'storage': {},
        'source': 'amm.org.gt',
    }

    # Fill datetime variable
    data['datetime'] = arrow.get(date, 'DD/MM/YYYY').replace(tzinfo=tz_gt, hour=hour).datetime

    # First add 'Biomasa' and 'Biogas' together to make 'biomass' variable (and avoid negative
    # values)
    data['production']['biomass'] = max(obj[obj['tipo'] == 'Biomasa'].potencia.iloc[0], 0) + max(obj[obj['tipo'] == 'Biogas'].potencia.iloc[0], 0)
    # Then fill the other sources directly with the MAP_GENERATION frame
    for i_type in MAP_GENERATION.keys():
        val = obj[obj['tipo'] == MAP_GENERATION[i_type]].potencia.iloc[0]
        if i_type == 'oil' and val > -1:
            # Set to 0 values that are not too small
            val = max(0, val)
        data['production'][i_type] = val

    return data


def fetch_production(zone_key='GT', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    # Define actual and last day (for midnight data)
    now = arrow.now(tz=tz_gt)
    formatted_date = now.format('DD/MM/YYYY')
    past_formatted_date = arrow.get(formatted_date, 'DD/MM/YYYY').shift(days=-1).format('DD/MM/YYYY')

    # Define output frame
    actual_hour = now.hour
    data = [dict() for h in range(actual_hour + 1)]

    # initial path for url to request
    url_init = 'http://wl.amm.org.gt/AMM_LectorDePotencias-AMM_GraficasWs-context-root/jersey/CargaPotencias/graficaAreaScada/'

    # Start with data for midnight
    url = url_init + past_formatted_date
    # Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = response.json()
    obj_df = pd.DataFrame(obj)
    obj_h = obj_df[obj_df.hora == '24']
    data_temp = fetch_hourly_production(zone_key, obj_h, 0, formatted_date)
    data[0] = data_temp

    # Fill data for the other hours until actual hour
    if actual_hour > 1:
        url = url_init + formatted_date
        # Request and rearange in DF
        r = session or requests.session()
        response = r.get(url)
        obj = response.json()
        obj_df = pd.DataFrame(obj)
        for h in range(1, actual_hour + 1):
            obj_h = obj_df[obj_df.hora == str(h)]
            data_temp = fetch_hourly_production(zone_key, obj_h, h, formatted_date)
            data[h] = data_temp

    return data


def fetch_hourly_consumption(zone_key, obj, hour, date):
    # output frame
    data = {
        'zoneKey': zone_key,
        'consumption': {},
        'source': 'amm.org.gt',
    }
    # Fill datetime variable
    data['datetime'] = arrow.get(date, 'DD/MM/YYYY').replace(tzinfo=tz_gt, hour=hour).datetime
    # Fill consumption variable
    data['consumption'] = obj[obj['tipo'] == 'Dem SNI'].potencia.iloc[0]

    return data


def fetch_consumption(zone_key='GT', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    # Define actual and last day (for midnight data)
    now = arrow.now(tz=tz_gt)
    formatted_date = now.format('DD/MM/YYYY')
    past_formatted_date = arrow.get(formatted_date, 'DD/MM/YYYY').shift(days=-1).format('DD/MM/YYYY')

    # Define output frame
    actual_hour = now.hour
    data = [dict() for h in range(actual_hour + 1)]

    # initial path for url to request
    url_init = 'http://wl.amm.org.gt/AMM_LectorDePotencias-AMM_GraficasWs-context-root/jersey/CargaPotencias/graficaAreaScada/'

    # Start with data for midnight
    url = url_init + past_formatted_date
    # Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = response.json()
    obj_df = pd.DataFrame(obj)
    obj_h = obj_df[obj_df.hora == '24']
    data_temp = fetch_hourly_consumption(zone_key, obj_h, 0, formatted_date)
    data[0] = data_temp

    # Fill data for the other hours until actual hour
    if actual_hour > 1:
        url = url_init + formatted_date
        # Request and rearange in DF
        r = session or requests.session()
        response = r.get(url)
        obj = response.json()
        obj_df = pd.DataFrame(obj)
        for h in range(1, actual_hour + 1):
            obj_h = obj_df[obj_df.hora == str(h)]
            data_temp = fetch_hourly_consumption(zone_key, obj_h, h, formatted_date)
            data[h] = data_temp

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_consumption() ->')
    print(fetch_consumption())
