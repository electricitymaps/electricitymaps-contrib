#!/usr/bin/env python3

import logging
import datetime
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

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

def fetch_production(zone_key = 'JP-TK', target_datetime=None,
                 logger=logging.getLogger(__name__)):
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
    df = fetch_consumption(zone_key, target_datetime)
    df['imports'] = 0
    
    for zone in exch_map[zone_key]:
        df2 = occtonet.fetch_exchange(zone_key, zone, target_datetime)
        df2 = pd.DataFrame(df2)
        exchname = df2.loc[0, 'sortedZoneKeys']
    
        df2 = df2[['datetime', 'netFlow']]
        df2.columns = ['datetime', exchname]
    
        df = pd.merge(df,df2, how='inner', on='datetime')
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
          'datetime': df.loc[i, 'datetime'],
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


def fetch_consumption(zone_key='JP-TK', target_datetime=None,
                      logger=logging.getLogger(__name__)):
    
    datestamp = arrow.get(target_datetime).to('Asia/Tokyo').strftime('%Y%m%d')
    consumption_url = {
                   'JP-HKD': "".join(['http://denkiyoho.hepco.co.jp/area/data/juyo_01_',
                                      datestamp, '.csv']),
                   'JP-TH': "".join(['http://setsuden.tohoku-epco.co.jp/common/demand/juyo_02_',
                                      datestamp, '.csv']),
                   'JP-TK': 'http://www.tepco.co.jp/forecast/html/images/juyo-j.csv',
                   'JP-HR': "".join(['http://www.rikuden.co.jp/denki-yoho/csv/juyo_05_', datestamp,'.csv']),
                   'JP-CB': 'http://denki-yoho.chuden.jp/denki_yoho_content_data/juyo_cepco003.csv',
                   'JP-KN': 'http://www.kepco.co.jp/yamasou/juyo1_kansai.csv',
                   'JP-CG': "".join(['http://www.energia.co.jp/jukyuu/sys/juyo_07_', datestamp, '.csv']),
                   'JP-SK': 'http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv'
                   }
    
    if zone_key == 'JP-KN':
        startrow = 44
    else:
        startrow = 42
    
    df = pd.read_csv(consumption_url[zone_key], skiprows=[x for x in range(startrow)], encoding = 'shift-jis')
    df.columns = ['Date', 'Time', 'cons']
    df['cons'] = 10*df['cons']
    df = df.dropna()
    df['datetime'] = df.apply(parse_dt, axis=1)
    df = df[['datetime', 'cons']]
    
    return df

def parse_dt(row):
    return arrow.get(' '.join([row['Date'], row['Time']]).replace('/', '-'),'YYYY-M-D H:mm').replace(tzinfo='Asia/Tokyo').datetime
