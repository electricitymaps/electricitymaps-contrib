#!/usr/bin/env python3
# coding=utf-8

import arrow
import dateutil
import requests
from .lib.validation import validate
from logging import getLogger

tz = 'America/Lima'

MAP_GENERATION = {
    'DIESEL': 'oil',
    'RESIDUAL': 'biomass',
    'CARBÓN': 'coal',
    'GAS': 'gas',
    'HÍDRICO': 'hydro',
    'BIOGÁS': 'unknown',
    'BAGAZO': 'biomass',
    'SOLAR': 'solar',
    'EÓLICA': 'wind'
}


def parse_date(item):
    return arrow.get(item['Nombre'], 'YYYY/MM/DD hh:mm:ss').replace(tzinfo=dateutil.tz.gettz(tz))


def fetch_production(zone_key='PE', session=None, target_datetime=None, logger=getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional) -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
    Return:
    A list of dictionaries in the form:
    {
      'zoneKey': 'FR',
      'dt': '2017-01-01T00:00:00Z',
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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    r = session or requests.session()
    url = 'https://www.coes.org.pe/Portal/portalinformacion/generacion'

    current_date = arrow.now(tz=tz)

    today = current_date.format('DD/MM/YYYY')
    yesterday = current_date.shift(days=-1).format('DD/MM/YYYY')
    end_date = current_date.shift(days=+1).format('DD/MM/YYYY')

    # To guarantee a full 24 hours of data we must make 2 requests.

    response_today = r.post(url, data={
        'fechaInicial': today,
        'fechaFinal': end_date,
        'indicador': 0
    })

    response_yesterday = r.post(url, data={
        'fechaInicial': yesterday,
        'fechaFinal': today,
        'indicador': 0
    })

    data_today = response_today.json()['GraficoTipoCombustible']['Series']
    data_yesterday = response_yesterday.json()['GraficoTipoCombustible']['Series']
    raw_data = data_today + data_yesterday

    # Note: We receive MWh values between two intervals!
    interval_hours = (parse_date(raw_data[0]['Data'][1]) - parse_date(
        raw_data[0]['Data'][0])).total_seconds() / 3600

    data = []
    datetimes = []

    for series in raw_data:
        k = series['Name']
        if k not in MAP_GENERATION:
            logger.warning(f'Unknown production type "{k}" for Peru')
            continue
        for v in series['Data']:
            dt = parse_date(v)
            try:
                i = datetimes.index(dt)
            except ValueError:
                i = len(datetimes)
                datetimes.append(dt)
                data.append({
                    'zoneKey': zone_key,
                    'datetime': dt.datetime,
                    'production': {},
                    'source': 'coes.org.pe'
                })

            data[i]['production'][MAP_GENERATION[k]] = \
                data[i]['production'].get(MAP_GENERATION[k], 0) + v['Valor'] / interval_hours

    return list(filter(lambda x: validate(x, logger, required=['gas'], floor=0.0, ) is not None, data))


if __name__ == '__main__':
    print(fetch_production())
