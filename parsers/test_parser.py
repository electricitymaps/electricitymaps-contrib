import time

import arrow
import click

try:
    from parsers.read_parser_config import parser_key_to_dict
except:
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
    try:
        res_list = iter(res)
    except:
        res_list = []
    dts = [e['datetime'] for e in res_list]
    last_dt = max(dts)
    max_dt_warning = (' !!! >2h from now !!!'
                      if (arrow.utcnow() - last_dt).total_seconds() > 2 * 3600
                      else ' -- OK, <2h from now :)')

    print('\n'.join(['parser result:', res.__str__(),
                     '---------------------',
                     'took {:.2f}s'.format(elapsed_time),
                     f'min returned datetime: {min(dts)}',
                     f'max returned datetime: {last_dt} UTC {max_dt_warning}',
                     ]))



if __name__ == '__main__':
    print(test_parser())
