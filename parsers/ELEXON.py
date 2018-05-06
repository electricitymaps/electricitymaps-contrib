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
import dateutil

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
    response = response.content.decode()
    return response


def query_production(session, target_datetime=None):
    params = {
        'ServiceType': 'csv'
    }
    response = query_ELEXON('FUELINST', session, params, target_datetime)
    response = response.content.decode()
    return response


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
        logger.warning(
            'Expected {} fields in INTERFUELHH report, got {}'.format(
                EXPECTED_FIELDS['INTERFUELHH'], field_count
            )
        )

    for line in lines[1:-1]:
        fields = line.split(',')

        # create the datetime
        datetime = datetime_from_date_sp(fields[1], fields[2])

        data = {
            'sortedZoneKeys': exchange,
            'datetime': datetime,
            'source': 'bmreports.com'
        }

        # positive value implies import to GB
        multiplier = -1 if 'GB' in sorted_zone_keys[0] else 1
        data['netFlow'] = float(fields[EXCHANGES[exchange]]) * multiplier
        data_points.append(data)

    if not target_datetime:
        return data_points[-1]
    else:
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
        logger.warning(
            'Expected {} fields in FUELINST report, got {}'.format(
                EXPECTED_FIELDS['FUELINST'], field_count
            )
        )

    for line in lines[1:-1]:
        fields = line.split(',')

        # create the datetime
        datetime = datetime_from_date_sp(fields[1], fields[2])

        data = {
            'zoneKey': 'GB',
            'datetime': datetime,
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

    if not target_datetime:
        return data_points[-1]
    else:
        return data_points


def datetime_from_date_sp(date, sp):
    date = '{}-{}-{}'.format(date[:4], date[4:6], date[6:8])
    sp = int(sp)
    hour = str(int((sp - 1) / 2)).zfill(2)
    minute = '00' if sp % 2 == 1 else '30'
    date_str = '{} {}:{}'.format(date, hour, minute)
    datetime = arrow.get(date_str).replace(tzinfo=dateutil.tz.gettz('Europe/London'))
    return datetime.datetime


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
