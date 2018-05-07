#!/usr/bin/env python3
# coding=utf-8

"""
Parser that uses the ELEXON API to return the following data types.

Production
Exchanges

Documentation:
https://www.elexon.co.uk/wp-content/uploads/2017/06/
bmrs_api_data_push_user_guide_v1.1.pdf
"""

import os
import arrow
import logging
import requests
import datetime as dt

ELEXON_ENDPOINT = 'https://api.bmreports.com/BMRS/{}/v1'

FUELS = {
    'production': {
        'gas': [4, 11],
        'oil': 5,
        'coal': 6,
        'nuclear': 7,
        'wind': 8,
        'hydro': 10,
        'unknown': 12,
        'biomass': 17
    },
    'storage': {
        'hydro': 9
    }
}

EXCHANGES = {
    'FR->GB': 3,
    'GB-NIR->IE': 4,
    'GB->NL': 5,
    'GB->IE': 6
}

EXPECTED_FIELDS = {
    'FUELINST': 18,
    'INTERFUELHH': 7
}


def query_ELEXON(report, session, params, target_datetime=None,
                 span=(-48, 24)):
    if target_datetime is None:
        target_datetime = arrow.utcnow().to('Europe/London')
    else:
        # make sure we have an arrow object
        target_datetime = arrow.get(target_datetime).to('Europe/London')

    params['FromDate'] = target_datetime.replace(
        hours=span[0]).format('YYYY-MM-DD')
    params['ToDate'] = target_datetime.replace(
        hours=span[1]).format('YYYY-MM-DD')

    if 'ELEXON_TOKEN' not in os.environ:
        raise Exception('No ELEXON_TOKEN found! Please add it to secrets.env!')
    params['APIKey'] = os.environ['ELEXON_TOKEN']
    return session.get(ELEXON_ENDPOINT.format(report), params=params)


def query_exchange(session, target_datetime=None):
    params = {
        'ServiceType': 'csv'
    }
    response = query_ELEXON('INTERFUELHH', session, params, target_datetime)
    return response.text


def query_production(session, target_datetime=None):
    params = {
        'ServiceType': 'csv'
    }
    response = query_ELEXON('FUELINST', session, params, target_datetime)
    return response.text


def parse_exchange(zone_key1, zone_key2, csv_text, target_datetime=None,
                   logger=logging.getLogger(__name__)):
    if not csv_text:
        return None

    sorted_zone_keys = sorted([zone_key1, zone_key2])

    exchange = '->'.join(sorted_zone_keys)
    data_points = list()
    lines = csv_text.split('\n')

    # check field count in report is as expected
    field_count = len(lines[1].split(','))
    if field_count != EXPECTED_FIELDS['INTERFUELHH']:
        raise ValueError(
            'Expected {} fields in INTERFUELHH report, got {}'.format(
                EXPECTED_FIELDS['INTERFUELHH'], field_count))

    for line in lines[1:-1]:
        fields = line.split(',')

        # settlement date / period combinations are always local time
        date = dt.datetime.strptime(fields[1], '%Y%m%d').date()
        settlement_period = int(fields[2])
        datetime = datetime_from_date_sp(date, settlement_period)

        data = {
            'sortedZoneKeys': exchange,
            'datetime': datetime,
            'source': 'bmreports.com'
        }

        # positive value implies import to GB
        multiplier = -1 if 'GB' in sorted_zone_keys[0] else 1
        data['netFlow'] = float(fields[EXCHANGES[exchange]]) * multiplier
        data_points.append(data)

    return data_points


def parse_production(csv_text, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    if not csv_text:
        return None

    data_points = list()
    lines = csv_text.split('\n')

    # check field count in report is as expected
    field_count = len(lines[1].split(','))
    if field_count != EXPECTED_FIELDS['FUELINST']:
        raise ValueError(
            'Expected {} fields in FUELINST report, got {}'.format(
                EXPECTED_FIELDS['FUELINST'], field_count))

    for line in lines[1:-1]:
        fields = line.split(',')

        # all timestamps are always GMT in ELEXON.
        # the publish time of a datapoint is five minutes after that
        # datapoint e.g. datapoint of 09:00 has a publish time of 09:05
        publish_time = fields[3]
        date_obj = dt.datetime.strptime(publish_time, '%Y%m%d%H%M%S')
        datetime = arrow.get(date_obj).replace(minutes=-5).to('Europe/London')

        data = {
            'zoneKey': 'GB',
            'datetime': datetime.datetime,
            'production': {},
            'storage': {},
            'source': 'bmreports.com'
        }

        # read the fuel values into the datapoint
        for _type, fuels in FUELS.items():
            for fuel, field_nums in fuels.items():
                if not isinstance(field_nums, list):
                    field_nums = [field_nums, ]
                data[_type][fuel] = sum([float(fields[i]) for i in field_nums])

        data_points.append(data)

    return data_points


def datetime_from_date_sp(date, sp):
    datetime = arrow.get(date).shift(minutes=30 * (sp - 1))
    return datetime.replace(tzinfo='Europe/London').datetime


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None,
                   logger=logging.getLogger(__name__)):
    session = session or requests.session()
    response = query_exchange(session, target_datetime)
    data = parse_exchange(zone_key1, zone_key2, response, target_datetime,
                          logger)
    return data


def fetch_production(session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    session = session or requests.session()
    response = query_production(session, target_datetime)
    data = parse_production(response, target_datetime, logger)
    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy 
    for testing."""

    print('fetch_production() ->')
    print(fetch_production())

    print('fetch_exchange(FR, GB) ->')
    print(fetch_exchange('FR', 'GB'))

    print('fetch_exchange(GB, IE) ->')
    print(fetch_exchange('GB', 'IE'))

    print('fetch_exchange(GB, NL) ->')
    print(fetch_exchange('GB', 'NL'))

    print('fetch_exchange(GB-NIR, IE) ->')
    print(fetch_exchange('GB-NIR', 'IE'))
