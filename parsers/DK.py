import logging
import datetime
import numpy as np
import pandas as pd
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests


ids = {'real_time':'06380963-b7c6-46b7-aec5-173d15e4648b',
       'energy_bal':'02356e88-7c4e-4ee9-b896-275d217cc1b9'}

def fetch_production(zone_key='DK-DK1', session=None,target_datetime=None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    """
    Queries energinet 5-minute frequency real-time data
    Tries to estimate conventional generation by type from
    energy balance of last 8 hours and retrospectively
    corrects the estimate when fuel data becomes available (-2hrs)
    """
    r = session or requests.session()
    
    
    
    if zone_key not in ['DK-DK1', 'DK-DK2']:
        raise NotImplementedError(
            'fetch_production() for {} not implemented'.format(zone_key))
    
    zone = zone_key[-3:]
    
    timestamp = arrow.get(target_datetime).strftime('%Y-%m-%d %H:%M')
    timestamp2 = timestamp[:-2] + '00'
    
    # fetch real-time/5-min data
    sqlstr1 = ''.join(['SELECT "Minutes5UTC" as timestamp, "ProductionGe100MW", "ProductionLt100MW",',
                      '("OffshoreWindPower"%2B"OnshoreWindPower") as wind, ',
                      '"SolarPower" as solar from "{}" '.format(ids['real_time']),
                      'WHERE "PriceArea" = \'{}\' AND '.format(zone),
                      '"Minutes5UTC" >= (timestamp\'{}\'-INTERVAL \'8 hours\') AND '.format(timestamp2),
                      '"Minutes5UTC" <= timestamp\'{}\' '.format(timestamp),
                      'ORDER BY "Minutes5UTC" ASC'])

    url1 = 'https://api.energidataservice.dk/datastore_search_sql?sql={}'.format(sqlstr1)
    
    response = r.get(url1)
    
    assert response.status_code == 200 and response.json() != [], \
        'Exception when fetching production for ' \
        '{}: error when calling url={}'.format(zone_key, url1)
        
    df = pd.DataFrame(response.json()['result']['records'])
    # index response dataframe by time
    df = df.set_index('timestamp')
    df.index = pd.DatetimeIndex(df.index)
    # add timestamps rounded to starting hour for retrospectively
    # correcting energy balance
    df['floor_ts'] = df.index.floor("H")
    df['conventional'] = df['ProductionGe100MW']+df['ProductionLt100MW']
    
    # resample to hourly frequency to fit to energy balance data
    df_rt_1h = df.resample('1h').mean()
    
    
    # fetch hourly energy balance from recent hours
    sqlstr2 = ''.join(['SELECT "HourUTC" as timestamp, "Biomass", "Waste", ',
                       '"OtherRenewable", "FossilGas" as Gas, "FossilHardCoal" as Coal, ',
                       '"FossilOil" as Oil, "HydroPower" as Hydro from "{}" '.format(ids['energy_bal']),
                       'WHERE "PriceArea" = \'{}\' AND '.format(zone),
                       '"HourUTC" >= (timestamp\'{}\'-INTERVAL \'8 hours\') AND '.format(timestamp2),
                       '"HourUTC" <= timestamp\'{}\' '.format(timestamp),
                       'ORDER BY "HourUTC" ASC'
                      ])
    
    url2 = 'https://api.energidataservice.dk/datastore_search_sql?sql={}'.format(sqlstr2)
    
    response = r.get(url2)
    
    assert response.status_code == 200 and response.json() != [], \
        'Exception when fetching production for ' \
        '{}: error when calling url={}'.format(zone_key, url2)
        
    df2 = pd.DataFrame(response.json()['result']['records'])
    # index response dataframe by time
    df2 = df2.set_index('timestamp')
    df2.index = pd.DatetimeIndex(df2.index)
    # drop empty rows from energy balance
    df2.dropna(how='all', inplace=True)
    
    # merge energy balance with recent real-time data
    df_1h = df_rt_1h.merge(df2, left_index=True, right_index=True)
    
    # replace nan values with 0
    df_1h.fillna(value=0, inplace=True)
    # Divide waste into 50% renewable and 50% non-renewable parts
    df_1h['unknown'] = 0.5*df_1h['Waste']
    df_1h['biomass'] = df_1h.filter(['Biomass', 'unknown', 'OtherRenewable']).sum(axis=1)
    
    
    fuels = ['biomass', 'coal', 'oil', 'gas', 'unknown', 'hydro']
    
    # Fit energy balance against recent real-time data grouped by hour
    for f in fuels:
        result = np.linalg.lstsq(df_1h[['ProductionGe100MW', 'ProductionLt100MW']].values, df_1h[f].values)
          
        # Apply results to 5-min frequency data, disallow negative values
        df[f] = df['ProductionGe100MW']*result[0][0]+df['ProductionLt100MW']*result[0][1]
        df.loc[df[f]<0,f] = 0
    
    df['conv_est'] = df.filter(fuels).sum(axis=1)
    # Scale the fuel estimates back to reported Production>=100MW, Production<100MW values
    for f in fuels:
        for dt in df.index:
            if df.loc[dt, 'conv_est'] > 0:
                df.loc[dt, f] = df.loc[dt, f]*df.loc[dt,'conventional']/df.loc[dt, 'conv_est']
        # Scale historical values to energy balance for hours old enough to have fuel data
        for h in df_1h.index:
        
            hr_ind = (df['floor_ts']==h)
            if df_1h.loc[h,'conventional'] >  0:
                df.loc[hr_ind, f] = df.loc[hr_ind, 'conventional']*df_1h.loc[h,f]/df_1h.loc[h,'conventional']
            
    # Format output as a list of dictionaries
    output = []
    for dt in df.index:
        
        data = {
              'zoneKey': zone_key,
              'datetime': None,
              'production': {
                  'biomass': 0,
                  'coal': 0,
                  'gas': 0,
                  'hydro': None,
                  'nuclear': 0,
                  'oil': 0,
                  'solar': None,
                  'wind': None,
                  'geothermal': None,
                  'unknown': 0
              },
              'storage': {},
              'source': 'api.energidataservice.dk'
            }
        
        data['datetime'] = dt.to_pydatetime()
        for f in ['solar', 'wind']+fuels:
            data['production'][f] = round(df.loc[dt,f],2)
        output.append(data)
    return output

def fetch_exchange(zone_key1='DK-DK1', zone_key2='DK-DK2', session=None,
                   target_datetime=None, logger=logging.getLogger(__name__)):
    
    
    r = session or requests.session()
    sorted_keys = '->'.join(sorted([zone_key1, zone_key2]))
    
    # pick the correct zone to search
    if 'DK1' in sorted_keys and 'DK2' in sorted_keys:
        zone = 'DK1'
    elif 'DK1' in sorted_keys:
        zone = 'DK1'
    elif 'DK2' in sorted_keys:
        zone = 'DK2'
    else:
        raise NotImplementedError(
            'Only able to fetch exchanges for Danish bidding zones')
    
   
    exch_map = {
        'DE->DK-DK1':'"ExchangeGermany"',
        'DE->DK-DK2':'"ExchangeGermany"',
        'DK-DK1->DK-DK2':'"ExchangeGreatBelt"',
        'DK-DK1->NO':'"ExchangeNorway"',
        'DK-DK1->NO-NO2':'"ExchangeNorway"',
        'DK-DK1->NL':'"ExchangeNetherlands"',
        'DK-DK1->SE':'"ExchangeSweden"',
        'DK-DK1->SE-SE3':'"ExchangeSweden"',
        'DK-DK2->SE':'"ExchangeSweden"',
        'DK-DK2->SE-SE4':'"ExchangeSweden"'
        
    }
    if sorted_keys not in exch_map:
        raise NotImplementedError(
            'Exchange {} not implemented'.format(sorted_keys))
    
    timestamp = arrow.get(target_datetime).strftime('%Y-%m-%d %H:%M')
    
    
    
    
    # fetch real-time/5-min data
    sqlstr = ''.join(['SELECT "Minutes5UTC" as timestamp, {} as "netFlow" '.format(exch_map[sorted_keys]),
                       'from "{}" '.format(ids['real_time']),
                       'WHERE "PriceArea" = \'{}\' AND '.format(zone),
                       '"Minutes5UTC" >= (timestamp\'{}\'-INTERVAL \'8 hours\') AND '.format(timestamp),
                       '"Minutes5UTC" <= timestamp\'{}\' '.format(timestamp),
                       'ORDER BY "Minutes5UTC" ASC'])

    url = 'https://api.energidataservice.dk/datastore_search_sql?sql={}'.format(sqlstr)
    
    response = r.get(url)
    
    assert response.status_code == 200 and response.json() != [], \
        'Exception when fetching flow for ' \
        '{}: error when calling url={}'.format(sorted_keys, url)
        
    df = pd.DataFrame(response.json()['result']['records'])
    df = df.set_index('timestamp')
    df.index = pd.DatetimeIndex(df.index)
    # drop empty rows
    df.dropna(how='all', inplace=True)
    
    # all exchanges are reported as net import,
    # where as eMap expects net export from
    # the first zone in alphabetical order
    if 'DE' not in sorted_keys:
        df['netFlow'] = -1*df['netFlow']
    # Format output
    output = []
    for dt in df.index:
        
        data = {
            'sortedZoneKeys': sorted_keys,
            'datetime': None,
            'netFlow': None,
            'source': 'api.energidataservice.dk'
        }
        
        data['datetime'] = dt.to_pydatetime()
        data['netFlow'] = df.loc[dt,'netFlow']
        output.append(data)
    return output

if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(DK-DK2, SE-SE4) ->')
    print(fetch_exchange('DK-DK2', 'SE-SE4'))
      
