
from datetime import datetime as dt
import logging

import arrow
import pandas as pd
import requests


def fetch_production(zone_key='GE', session=None, target_datetime: dt=None,
                     logger: logging.Logger=None):
    """
    Requests the last known production mix (in MW) of a given country.
    """
    r = session or requests.session()
    
    if target_datetime is None:
        prod_map = {'hydroData':'hydro','solarData':'solar',
           'thermalData':'gas', 'windPowerData':'wind'}
    
    
        url = 'http://www.gse.com.ge/apps/gsebackend/rest/map'
        response = r.get(url)
        obj = response.json()

        obj['typeSum']['timestamp']=arrow.now('Asia/Tbilisi').floor('minute').datetime

        data = {
        'zoneKey': 'GE',
        'production': {},
        'storage': {},
        'source': 'gse.com.ge',
        }

        for key, value in obj['typeSum'].items():
            # All production values should be >= 0
            # Should be a floating point value
            if key in list(prod_map.keys()):
                if value>=0:
                    data['production'][prod_map[key]] = value
                else:
                    data['production'][prod_map[key]] = None
                
        data['datetime'] = obj['typeSum']['timestamp']
    
        return data
    else:
        # Format url
        date = arrow.get(target_datetime).to('Asia/Tbilisi')
        formatted_from = date.format('YYYY-MM-DDT00:00:00')
        formatted_to   = date.format('YYYY-MM-DDT23:00:00')
        base_url = 'http://gse.com.ge/apps/gsebackend/rest/diagramDownload'
        url_parameters = '?fromDate={}.0000Z&' \
                         'toDate={}.0000Z&type=FACT&lang=EN'.format(
                         formatted_from, formatted_to)
        url = base_url + url_parameters
        # Download the xls file and parse the table it contains
        data = pd.read_excel(url, skiprows=2).iloc[2:6, 3:27]
        data.index = [ 'gas', 'hydro', 'wind', 'solar' ]
        data.columns = pd.date_range(start=formatted_from,
                                     end=formatted_to,
                                     freq='1H')
        data = data.dropna(axis=1)
        # Create list of dictionaries with production data
        production_mix_by_hour = []
        for hour, datapoint in data.items():
            production_mix = {
                'zoneKey': zone_key,
                'datetime': arrow.get(hour, 'Asia/Tbilisi').datetime,
                'production': {
                    'gas'   : datapoint['gas'],
                    'hydro' : datapoint['hydro'],
                    'wind'  : datapoint['wind'],
                    'solar' : datapoint['solar']
                },
                'source': 'gse.com.ge'
            }
            production_mix_by_hour.append(production_mix)
        # Return production data for the entire day of the requested
        # target_datetime
        return production_mix_by_hour

def fetch_exchange(zone_key1='GE', zone_key2='TR', session=None, target_datetime=None,
                   logger=None):
    """
    Requests the last known power exchange (in MW) between two countries.
    """
    
    exch_map = {'AM->GE':'armeniaSum', 'AZ->GE':'azerbaijanSum',
            'GE->TR':'turkeySum'}
    
    r = session or requests.session()
    
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    else:    
        url = 'http://www.gse.com.ge/apps/gsebackend/rest/map'
        response = r.get(url)
        obj = response.json()
    
        exch = '->'.join(sorted([zone_key1, zone_key2]))
                     
        data = {
            'sortedZoneKeys': exch,
            'source': 'gse.com.ge',
        }
    
    
        # The net flow to be reported should be from the first country to the second
        # (sorted alphabetically). This is NOT necessarily the same direction as the flow
        # from country1 to country2                 
        if exch == 'AM->GE':
            data['netFlow'] = obj['areaSum']['armeniaSum']
        elif exch == 'AZ->GE':
            data['netFlow'] = obj['areaSum']['azerbaijanSum']
        # GE->RU might be falsely reported, exchanges.json has a definition to use the Russian TSO for this flow
        elif exch == 'GE->RU':
            netFlow = -obj['areaSum']['russiaSum']-obj['areaSum']['russiaJavaSum']-obj['areaSum']['russiaSalkhinoSum']
            data['netFlow'] = netFlow
            #data['netFlow'] = None
        elif exch == 'GE->TR':
            data['netFlow'] = -obj['areaSum']['turkeySum']
        else:
            raise NotImplementedError('This exchange pair is not implemented.')
        

        data['datetime']=arrow.now('Asia/Tbilisi').floor('minute').datetime
    
        return data
    
    
if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_exchange(GE, AM) ->')
    print(fetch_exchange('GE', 'AM'))
    print('fetch_exchange(GE, AZ) ->')
    print(fetch_exchange('GE', 'AZ'))
    print('fetch_exchange(GE, RU) ->')
    print(fetch_exchange('GE', 'RU'))
    print('fetch_exchange(GE, TR) ->')
    print(fetch_exchange('GE', 'TR'))
    
