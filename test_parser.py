#!/usr/bin/env python3

from parsers.lib.quality import validate_consumption, validate_production, validate_exchange, ValidationError
import time

import arrow
import click
import datetime

from utils.parsers import PARSER_KEY_TO_DICT


@click.command()
@click.argument('zone')
@click.argument('data-type', default='production')
@click.option('--target_datetime', default=None, show_default=True)
def test_parser(zone, data_type, target_datetime):
    """

    Parameters
    ----------
    zone: a two letter zone from the map
    data_type: in ['production', 'exchangeForecast', 'production', 'exchange',
      'price', 'consumption', 'generationForecast', 'consumptionForecast']
    target_datetime: string parseable by arrow, such as 2018-05-30 15:00

    Examples
    -------
    >>> python test_parser.py NO-NO3-\>SE exchange
    parser result:
    {'netFlow': -51.6563, 'datetime': datetime.datetime(2018, 7, 3, 14, 38, tzinfo=tzutc()), 'source': 'driftsdata.stattnet.no', 'sortedZoneKeys': 'NO-NO3->SE'}
    ---------------------
    took 0.09s
    min returned datetime: 2018-07-03 14:38:00+00:00
    max returned datetime: 2018-07-03T14:38:00+00:00 UTC  -- OK, <2h from now :) (now=2018-07-03T14:39:16.274194+00:00 UTC)
    >>> python test_parser.py FR production
    parser result:
    [... long stuff ...]
    ---------------------
    took 5.38s
    min returned datetime: 2018-07-02 00:00:00+02:00
    max returned datetime: 2018-07-03T14:30:00+00:00 UTC  -- OK, <2h from now :) (now=2018-07-03T14:43:35.501375+00:00 UTC)
    """
    if target_datetime:
        target_datetime = arrow.get(target_datetime).datetime
    start = time.time()

    parser = PARSER_KEY_TO_DICT[data_type][zone]
    if data_type in ['exchange', 'exchangeForecast']:
        args = zone.split('->')
    else:
        args = [zone]
    res = parser(*args, target_datetime=target_datetime)

    if not res:
        print('Error: parser returned nothing ({})'.format(res))
        return

    elapsed_time = time.time() - start
    if isinstance(res, (list, tuple)):
        res_list = list(res)
    else:
        res_list = [res]

    try:
        dts = [e['datetime'] for e in res_list]
    except:
        print('Parser output lacks `datetime` key for at least some of the '
              'ouput. Full ouput: \n\n{}\n'.format(res))
        return
    
    assert all([type(e['datetime']) is datetime.datetime for e in res_list]), \
        'Datetimes must be returned as native datetime.datetime objects'

    last_dt = arrow.get(max(dts)).to('UTC')
    first_dt = arrow.get(min(dts)).to('UTC')
    max_dt_warning = ''
    if not target_datetime:
        max_dt_warning = (
            ' :( >2h from now !!!'
            if (arrow.utcnow() - last_dt).total_seconds() > 2 * 3600
            else ' -- OK, <2h from now :) (now={} UTC)'.format(arrow.utcnow()))

    print('\n'.join(['parser result:', res.__str__(),
                     '---------------------',
                     'took {:.2f}s'.format(elapsed_time),
                     'min returned datetime: {} UTC'.format(first_dt),
                     'max returned datetime: {} UTC {}'.format(
                         last_dt, max_dt_warning), ]))
    
    try:
        if data_type == 'production':
            validate_production(res, zone)
        elif data_type == 'consumption':
            validate_consumption(res, zone)
        elif data_type == 'exchange':
            validate_exchange(res, zone)
    except ValidationError as e:
        print('\nValidation failed: {}'.format(e))

    

if __name__ == '__main__':
    print(test_parser())
