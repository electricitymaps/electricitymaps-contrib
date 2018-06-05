import time

import arrow
import click

try:
    from parsers.read_parser_config import parser_key_to_dict
except Exception:
    raise ValueError("couldn't do a local import. Please run from the"
                     "`electricitymap` folder: python parsers/test_parser.py "
                     "[OPTIONS] ZONE [DATA_TYPE]")


@click.command()
@click.argument('zone')
@click.argument('data-type', default='production')
@click.option('--target_datetime', default=None, show_default=True)
def test_parser(zone, data_type, target_datetime):
    if target_datetime:
        target_datetime = arrow.get(target_datetime).datetime
    start = time.time()
    parser = parser_key_to_dict[data_type][zone]
    res = parser(zone, target_datetime=target_datetime)
    elapsed_time = time.time() - start
    if isinstance(res, (list, tuple)):
        res_list = iter(res)
    else:
        res_list = [res]
    dts = [e['datetime'] for e in res_list]
    last_dt = arrow.get(max(dts)).to('UTC')
    max_dt_warning = (
        ' :( >2h from now !!!'
        if (arrow.utcnow() - last_dt).total_seconds() > 2 * 3600
        else ' -- OK, <2h from now :) (now={} UTC)'.format(arrow.utcnow()))

    print('\n'.join(['parser result:', res.__str__(),
                     '---------------------',
                     'took {:.2f}s'.format(elapsed_time),
                     'min returned datetime: {}'.format(min(dts)),
                     'max returned datetime: {} UTC {}'.format(
                         last_dt, max_dt_warning), ]))



if __name__ == '__main__':
    print(test_parser())
