#!/usr/bin/python
# -*- coding: utf-8 -*-

import arrow
import dateutil
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

def validate(datapoint):
    if sum([v for k,v in datapoint['production'].iteritems() if v is not None]) > 0 \
        and datapoint['production'].get('gas', None) is not None:
        return datapoint
    else:
        return None

def parse_date(item):
    return arrow.get(item['Nombre'], 'M/D/YYYY h:mm:ss A').replace(tzinfo=dateutil.tz.gettz(tz))

def fetch_production(country_code='PE', session=None):
    r = session or requests.session()
    url = 'http://www.coes.org.pe/Portal/portalinformacion/Generacion'
    response = r.post(url, data={
      'fechaInicial': arrow.now(tz=tz).format('DD/MM/YYYY'),
      'fechaFinal': arrow.now(tz=tz).replace(days=+1).format('DD/MM/YYYY'),
      'indicador': 0
    })
    obj = response.json()['GraficoTipoCombustible']['Series']

    # Note: We receive MWh values between two intervals!
    interval_hours = (parse_date(obj[0]['Data'][1]) - parse_date(obj[0]['Data'][0])).total_seconds() / 3600

    data = []
    datetimes = []

    for serie in obj:
        k = serie['Name'].encode('utf-8')
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
                    'countryCode': country_code,
                    'datetime': datetime.datetime,
                    'production': {},
                    'source': 'coes.org.pe'
                })

            data[i]['production'][MAP_GENERATION[k]] = \
                data[i]['production'].get(MAP_GENERATION[k], 0) + v['Valor'] / interval_hours

    return filter(lambda x: validate(x) is not None, data)


if __name__ == '__main__':
    print fetch_production()
