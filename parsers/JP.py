#!/usr/bin/env python3
# coding=utf-8
import logging
# The arrow library is used to handle datetimes
import arrow
import pandas as pd
from . import occtonet

# Abbreviations
# JP-HKD : Hokkaido
# JP-TH  : Tohoku
# JP-TK  : Tokyo area
# JP-CB  : Chubu
# JP-HR  : Hokuriku
# JP-KN  : Kansai
# JP-SK  : Shikoku
# JP-KY  : Kyushu
# JP-ON  : Okinawa

def fetch_production(zone_key='JP-TK', session=None, target_datetime=None,
                     logger=logging.getLogger(__name__)):
    """
    Calculates production from consumption and imports for a given area
    All production is mapped to unknown
    """
    if target_datetime:
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')
    exch_map = {
        'JP-HKD':['JP-TH'],
        'JP-TH':['JP-TK'],
        'JP-TK':['JP-TH', 'JP-CB'],
        'JP-CB':['JP-TK', 'JP-HR', 'JP-KN'],
        'JP-HR':['JP-CB', 'JP-KN'],
        'JP-KN':['JP-CB', 'JP-HR', 'JP-SK', 'JP-CG'],
        'JP-SK':['JP-KN', 'JP-CG'],
        'JP-CG':['JP-KN', 'JP-SK', 'JP-KY']
        }
    df = fetch_consumption_df(zone_key, target_datetime)
    df['imports'] = 0
    for zone in exch_map[zone_key]:
        df2 = occtonet.fetch_exchange(zone_key, zone, target_datetime)
        df2 = pd.DataFrame(df2)
        exchname = df2.loc[0, 'sortedZoneKeys']
        df2 = df2[['datetime', 'netFlow']]
        df2.columns = ['datetime', exchname]
        df = pd.merge(df, df2, how='inner', on='datetime')
        if exchname.split('->')[-1] == zone_key:
            df['imports'] = df['imports']+df[exchname]
        else:
            df['imports'] = df['imports']-df[exchname]
    df['prod'] = df['cons']-df['imports']
    df = df[['datetime', 'prod']]
    # add a row to production for each entry in the dictionary:
    sources = {
        'JP-HKD':'denkiyoho.hepco.co.jp',
        'JP-TH':'setsuden.tohoku-epco.co.jp',
        'JP-TK':'www.tepco.co.jp',
        'JP-CB':'denki-yoho.chuden.jp',
        'JP-HR':'www.rikuden.co.jp/denki-yoho',
        'JP-KN':'www.kepco.co.jp',
        'JP-SK':'www.energia.co.jp',
        'JP-CG':'www.yonden.co.jp'
        }
    datalist = []
    for i in range(df.shape[0]):
        data = {
            'zoneKey': zone_key,
            'datetime': df.loc[i, 'datetime'].to_pydatetime(),
            'production': {
                'biomass': None,
                'coal': None,
                'gas': None,
                'hydro': None,
                'nuclear': None,
                'oil': None,
                'solar': None,
                'wind': None,
                'geothermal': None,
                'unknown': df.loc[i, 'prod']
            },
            'storage': {},
            'source': ['occtonet.or.jp', sources[zone_key]]
            }
        datalist.append(data)
    return datalist


def fetch_consumption_df(zone_key='JP-TK', target_datetime=None,
                      logger=logging.getLogger(__name__)):
    """
    Returns the consumption for an area as a pandas DataFrame
    """
    datestamp = arrow.get(target_datetime).to('Asia/Tokyo').strftime('%Y%m%d')
    consumption_url = {
        'JP-HKD': 'http://denkiyoho.hepco.co.jp/area/data/juyo_01_{}.csv'.format(datestamp),
        'JP-TH': 'http://setsuden.tohoku-epco.co.jp/common/demand/juyo_02_{}.csv'.format(datestamp),
        'JP-TK': 'http://www.tepco.co.jp/forecast/html/images/juyo-j.csv',
        'JP-HR': 'http://www.rikuden.co.jp/denki-yoho/csv/juyo_05_{}.csv'.format(datestamp),
        'JP-CB': 'http://denki-yoho.chuden.jp/denki_yoho_content_data/juyo_cepco003.csv',
        'JP-KN': 'http://www.kepco.co.jp/yamasou/juyo1_kansai.csv',
        'JP-CG': 'http://www.energia.co.jp/jukyuu/sys/juyo_07_{}.csv'.format(datestamp),
        'JP-SK': 'http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv'
        }
    # First roughly 40 rows of the consumption files have hourly data,
    # the parser skips to the rows with 5-min actual values 
    if zone_key == 'JP-KN':
        startrow = 44
    else:
        startrow = 42
    df = pd.read_csv(consumption_url[zone_key], skiprows=list(range(startrow)),
                     encoding='shift-jis')
    df.columns = ['Date', 'Time', 'cons']
    # Convert 万kW to MW
    df['cons'] = 10*df['cons']
    df = df.dropna()
    df['datetime'] = df.apply(parse_dt, axis=1)
    df = df[['datetime', 'cons']]
    return df

def parse_dt(row):
    """
    Parses timestamps from date and time
    """
    return arrow.get(' '.join([row['Date'], row['Time']]).replace('/', '-'),
                     'YYYY-M-D H:mm').replace(tzinfo='Asia/Tokyo').datetime

if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
