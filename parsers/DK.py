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
    Queries "Electricity balance Non-Validated" from energinet api
    for Danish bidding zones
    """
    r = session or requests.session()
    
    
    
    if zone_key not in ['DK-DK1', 'DK-DK2']:
        raise NotImplementedError(
            'fetch_production() for {} not implemented'.format(zone_key))
    
    zone = zone_key[-3:]
    
    timestamp = arrow.get(target_datetime).strftime('%Y-%m-%d %H:%M')
    
    # fetch hourly energy balance from recent hours
    sqlstr = 'SELECT "HourUTC" as timestamp, "Biomass", "Waste", \
                     "OtherRenewable", "FossilGas" as gas, "FossilHardCoal" as coal, \
                     "FossilOil" as oil, "HydroPower" as hydro, \
                     ("OffshoreWindPower"%2B"OnshoreWindPower") as wind, \
                     "SolarPower" as solar from "{0}" \
                     WHERE "PriceArea" = \'{1}\' AND \
                     "HourUTC" >= (timestamp\'{2}\'-INTERVAL \'8 hours\') AND \
                     "HourUTC" <= timestamp\'{2}\' \
                     ORDER BY "HourUTC" ASC'.format(ids['energy_bal'], zone, timestamp)
                     
    
    url = 'https://api.energidataservice.dk/datastore_search_sql?sql={}'.format(sqlstr)
    
    response = r.get(url)
    
    assert response.status_code == 200 and response.json()['result']['records'] != [], \
        'Exception when fetching production for ' \
        '{}: error when calling url={}'.format(zone_key, url2)
        
    df = pd.DataFrame(response.json()['result']['records'])
    # index response dataframe by time
    df = df.set_index('timestamp')
    df.index = pd.DatetimeIndex(df.index)
    # drop empty rows from energy balance
    df.dropna(how='all', inplace=True)
    
    # Divide waste into 50% renewable and 50% non-renewable parts
    df['unknown'] = 0.5*df['Waste']
    df['biomass'] = df.filter(['Biomass', 'unknown', 'OtherRenewable']).sum(axis=1)
    
    fuels = ['biomass', 'coal', 'oil', 'gas', 'unknown', 'hydro']
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
            data['production'][f] = df.loc[dt,f]
        output.append(data)
    return output

def fetch_exchange(zone_key1='DK-DK1', zone_key2='DK-DK2', session=None,
                   target_datetime=None, logger=logging.getLogger(__name__)):
    
    """
    Fetches 5-minute frequency exchange data for Danish bidding zones
    from api.energidataservice.dk
    """
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
        'DK-DK1->NO-NO2':'"ExchangeNorway"',
        'DK-DK1->NL':'"ExchangeNetherlands"',
        'DK-DK1->SE':'"ExchangeSweden"',
        'DK-DK1->SE-SE3':'"ExchangeSweden"',
        'DK-DK2->SE-SE':'("ExchangeSweden" - "BornholmSE4")',# Exchange from Bornholm to Sweden is included in "ExchangeSweden"
        'DK-DK2->SE-SE4':'("ExchangeSweden" - "BornholmSE4")' #but Bornholm island is reported separately from DK-DK2 in eMap
         
    }
    if sorted_keys not in exch_map:
        raise NotImplementedError(
            'Exchange {} not implemented'.format(sorted_keys))
    
    timestamp = arrow.get(target_datetime).strftime('%Y-%m-%d %H:%M')
    
    
    
    
    # fetch real-time/5-min data
    sqlstr = 'SELECT "Minutes5UTC" as timestamp, {0} as "netFlow" \
                     from "{1}" WHERE "PriceArea" = \'{2}\' AND \
                     "Minutes5UTC" >= (timestamp\'{3}\'-INTERVAL \'8 hours\') AND \
                     "Minutes5UTC" <= timestamp\'{3}\' \
                     ORDER BY "Minutes5UTC" ASC'.format(exch_map[sorted_keys],
                                                        ids['real_time'],
                                                        zone,
                                                        timestamp)

    url = 'https://api.energidataservice.dk/datastore_search_sql?sql={}'.format(sqlstr)
    
    response = r.get(url)
    
    assert response.status_code == 200 and response.json()['result']['records'] != [], \
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
      
