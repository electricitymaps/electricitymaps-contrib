#!/usr/bin/env python3
# coding=utf-8
import logging
# The arrow library is used to handle datetimes
import arrow
import datetime as dt
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
# JP-CG  : Chūgoku

sources = {
        'JP-HKD':'denkiyoho.hepco.co.jp',
        'JP-TH':'setsuden.tohoku-epco.co.jp',
        'JP-TK':'www.tepco.co.jp',
        'JP-CB':'denki-yoho.chuden.jp',
        'JP-HR':'www.rikuden.co.jp/denki-yoho',
        'JP-KN':'www.kepco.co.jp',
        'JP-SK':'www.yonden.co.jp',
        'JP-CG':'www.energia.co.jp',
        'JP-KY':'www.kyuden.co.jp/power_usages/pc.html',
        'JP-ON':'www.okiden.co.jp/denki/'
        }

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
    # add a row to production for each entry in the dictionary:
    
    datalist = []
    #for i in range(df.shape[0]):
    for i in df.index:
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
        'JP-SK': 'http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv',
        'JP-KY': 'http://www.kyuden.co.jp/power_usages/csv/juyo-hourly-{}.csv'.format(datestamp),
        'JP-ON': 'https://www.okiden.co.jp/denki/juyo_10_{}.csv'.format(datestamp)
        }
    # First roughly 40 rows of the consumption files have hourly data,
    # the parser skips to the rows with 5-min actual values 
    if zone_key == 'JP-KN':
        startrow = 44
    else:
        startrow = 42
    df = pd.read_csv(consumption_url[zone_key], skiprows=startrow,
                     encoding='shift-jis')
    df.columns = ['Date', 'Time', 'cons']
    # Convert 万kW to MW
    df['cons'] = 10*df['cons']
    df = df.dropna()
    df['datetime'] = df.apply(parse_dt, axis=1)
    df = df[['datetime', 'cons']]
    return df

def fetch_consumption_forecast(zone_key='JP-KY', target_datetime=None,
                      logger=logging.getLogger(__name__)):
    """
    Gets consumption forecast for specified zone.
    Returns a list of dictionaries.
    """
    # Currently past dates not implemented for areas with no date in their demand csv files
    if target_datetime and (zone_key in ['JP-TK', 'JP-TH', 'JP-CB', 'JP-KN', 'JP-SK']):
        raise NotImplementedError(
            "Past dates not yet implemented for selected region")
    datestamp = arrow.get(target_datetime).to('Asia/Tokyo').strftime('%Y%m%d')
    # Forecasts ahead of current date are not available
    if datestamp > arrow.get().to('Asia/Tokyo').strftime('%Y%m%d'):
        raise NotImplementedError(
            "Future dates(local time) not implemented for selected region")
        
    consumption_url = {
                   'JP-HKD': 'http://denkiyoho.hepco.co.jp/area/data/juyo_01_{}.csv'.format(datestamp),
                   'JP-TH': 'http://setsuden.tohoku-epco.co.jp/common/demand/juyo_02_{}.csv'.format(datestamp),
                   'JP-TK': 'http://www.tepco.co.jp/forecast/html/images/juyo-j.csv',
                   'JP-HR': 'http://www.rikuden.co.jp/denki-yoho/csv/juyo_05_{}.csv'.format(datestamp),
                   'JP-CB': 'http://denki-yoho.chuden.jp/denki_yoho_content_data/juyo_cepco003.csv',
                   'JP-KN': 'http://www.kepco.co.jp/yamasou/juyo1_kansai.csv',
                   'JP-CG': 'http://www.energia.co.jp/jukyuu/sys/juyo_07_{}.csv'.format(datestamp),
                   'JP-SK': 'http://www.yonden.co.jp/denkiyoho/juyo_shikoku.csv',
                   'JP-KY': 'http://www.kyuden.co.jp/power_usages/csv/juyo-hourly-{}.csv'.format(datestamp),
                   'JP-ON': 'https://www.okiden.co.jp/denki/juyo_10_{}.csv'.format(datestamp)
                   }
    # Skip non-tabular data at the start of source files
    if zone_key == 'JP-KN':
        startrow = 9
    else:
        startrow = 7
    # Read the 24 hourly values
    df = pd.read_csv(consumption_url[zone_key],skiprows=startrow, nrows = 24, encoding = 'shift-jis')
    if zone_key == 'JP-KN':
        df = df[['DATE', 'TIME', '予想値(万kW)']]
    else:
        try:
            df = df[['DATE', 'TIME', '予測値(万kW)']]
        except KeyError:
            df = df[['DATE', 'TIME', '予測値（万kW)']]
    df.columns = ['Date', 'Time', 'fcst']

    df['datetime'] = df.apply(parse_dt, axis=1)

    # convert from 万kW to MW
    df['fcst'] = 10*df['fcst']
    # validate
    df = df.loc[df['fcst']>0]
    # return format
    data = []
    #for i in range(df.shape[0]):
    for i in df.index:
            data.append({
                'zoneKey': zone_key,
                'datetime': df.loc[i,'datetime'].to_pydatetime(),
                'value': df.loc[i,'fcst'],
                'source': sources[zone_key]
            })
    return data

def fetch_price(zone_key='JP-TK', session=None, target_datetime=None,
                logger=logging.getLogger(__name__)):
    if target_datetime is None:
        target_datetime = dt.datetime.now() + dt.timedelta(days=1)

    # price files contain data for fiscal year and not calendar year.
    if target_datetime.month <= 3:
        fiscal_year = target_datetime.year - 1
    else:
        fiscal_year = target_datetime.year
    url = 'http://www.jepx.org/market/excel/spot_{}.csv'.format(fiscal_year)
    df = pd.read_csv(url, encoding='shift-jis')

    df = df.iloc[:, [0, 1, 6, 7, 8, 9, 10, 11, 12, 13, 14]]
    df.columns = ['Date', 'Period', 'JP-HKD', 'JP-TH', 'JP-TK', 'JP-CB',
                  'JP-HR', 'JP-KN', 'JP-CG', 'JP-SK', 'JP-KY']

    if zone_key not in df.columns[2:]:
        return []

    start = target_datetime - dt.timedelta(days=1)
    df['Date'] = df['Date'].apply(lambda x: dt.datetime.strptime(x, '%Y/%m/%d'))
    df = df[(df['Date'] >= start.date()) & (df['Date'] <= target_datetime.date())]

    df['datetime'] = df.apply(lambda row: arrow.get(row['Date']).shift(
        minutes=30 * (row['Period'] - 1)).replace(tzinfo='Asia/Tokyo'), axis=1)

    data = list()
    for row in df.iterrows():
        data.append({
            'zoneKey': zone_key,
            'currency': 'JPY',
            'datetime': row[1]['datetime'].datetime,
            'price': round(int(1000*row[1][zone_key]),-1),# Convert from JPY/kWh to JPY/MWh
            'source': 'jepx.org'
        })

    return data


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
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_consumption_forecast() ->')
    print(fetch_consumption_forecast())
    print('fetch_consumption_forecast(JP-TH) ->')
    print(fetch_consumption_forecast('JP-TH'))
    print('fetch_consumption_forecast(JP-TK) ->')
    print(fetch_consumption_forecast('JP-TK'))
    print('fetch_consumption_forecast(JP-CB) ->')
    print(fetch_consumption_forecast('JP-CB'))
    print('fetch_consumption_forecast(JP-KN) ->')
    print(fetch_consumption_forecast('JP-KN'))
    print('fetch_consumption_forecast(JP-SK) ->')
    print(fetch_consumption_forecast('JP-SK'))
    print('fetch_consumption_forecast(JP-KY) ->')
    print(fetch_consumption_forecast('JP-KY'))
    print('fetch_consumption_forecast(JP-ON) ->')
    print(fetch_consumption_forecast('JP-ON'))
