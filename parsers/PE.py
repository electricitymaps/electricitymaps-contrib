#!/usr/bin/env python3
# coding=utf-8

import arrow
import dateutil
from .lib.validation import validate
import requests

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
    return arrow.get(item['Nombre'], 'M/D/YYYY h:mm:ss A').replace(tzinfo=dateutil.tz.gettz(tz))


def fetch_production(zone_key='PE', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    r = session or requests.session()
    url = 'http://www.coes.org.pe/Portal/portalinformacion/Generacion'
    response = r.post(url, data={
        'fechaInicial': arrow.now(tz=tz).format('DD/MM/YYYY'),
        'fechaFinal': arrow.now(tz=tz).replace(days=+1).format('DD/MM/YYYY'),
        'indicador': 0
    })
    obj = response.json()['GraficoTipoCombustible']['Series']

    # Note: We receive MWh values between two intervals!
    interval_hours = (parse_date(obj[0]['Data'][1]) - parse_date(
        obj[0]['Data'][0])).total_seconds() / 3600

    data = []
    datetimes = []

    for serie in obj:
        k = serie['Name']
        if not k in MAP_GENERATION:
            raise Exception('Unknown production type %s' % k)
        for v in serie['Data']:
            datetime = parse_date(v)
            try:
                i = datetimes.index(datetime)
            except ValueError:
                i = len(datetimes)
                datetimes.append(datetime)
                data.append({
                    'zoneKey': zone_key,
                    'datetime': datetime.datetime,
                    'production': {},
                    'source': 'coes.org.pe'
                })

            data[i]['production'][MAP_GENERATION[k]] = \
                data[i]['production'].get(MAP_GENERATION[k], 0) + v['Valor'] / interval_hours

    return list(filter(lambda x: validate(x, required=['gas'], floor=0.0, ) is not None, data))


if __name__ == '__main__':
    print(fetch_production())
