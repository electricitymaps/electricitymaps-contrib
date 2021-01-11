"""Parser for the Republic Of Ireland."""
import logging
from datetime import date, datetime, time, timedelta

import pandas as pd

import arrow
import requests


QUERY_ROOT = f'http://smartgriddashboard.eirgrid.com/DashboardService.svc/data?'

MAPPING = {'FUEL_COAL': 'coal',
           'FUEL_GAS': 'gas',
           'FUEL_RENEW': 'renew',
           'FUEL_OTHER_FOSSIL': 'unknown',
           }


def format_date_inputs(a_date):
    return a_date.strftime('%d-%b-%Y+%H:%M').replace(':', '%3A')


def fetch_production(zone_key='ROI', session=None,
                     target_datetime: datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):

    r = session or requests.session()

    if target_datetime is None:
        target_datetime = datetime.now()

    url = QUERY_ROOT + ''.join(f'&{query_key}={query_value}' for query_key, query_value
                               in {'area': 'fuelmix', 'region': zone_key,
                                   'datefrom': format_date_inputs(target_datetime - timedelta(minutes=15)),
                                   'dateto': format_date_inputs(target_datetime)}.items())

    res = r.get(url)
    obj = res.json()
    assert obj['Status'] == 'Success', 'Exception when fetching production for ' \
        '{}: error when calling url={}'.format(zone_key, url)

    data = {
        'zoneKey': zone_key,
        'production': {MAPPING[row['FieldName']]: float(row['Value']) for row in obj['Rows']
                       if row['FieldName'] in MAPPING},
        'storage': {},
        'source': 'smartgriddashboard.eirgrid.com',
        'datetme': datetime.strptime(obj['Rows'][0]['EffectiveTime'], '%d-%b-%Y %H:%M:%S').datetime,
    }

    return data
