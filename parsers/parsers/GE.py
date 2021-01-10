import logging
import datetime

import arrow
import requests

def fetch_production(zone_key='GE', session=None, target_datetime: datetime.datetime=None,
                     logger: logging.Logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. If past data is not available, raise a NotImplementedError. Beware that the
      provided target_datetime is UTC.
    logger: an instance of a `logging.Logger`. Information logged will be publicly available so that
      correct execution of the logger can be checked. All Exceptions will automatically be logged,
      so when something's wrong, simply raise an Exception (with an explicit text). Use
      `logger.warning` or `logger.info` for information that can useful to check if the parser is
      working correctly.
      
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
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
        raise NotImplementedError('This parser is not yet able to parse past dates')

def fetch_exchange(zone_key1='GE', zone_key2='TR', session=None, target_datetime=None,
                   logger=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not provided, we should
      default it to now. If past data is not available, raise a NotImplementedError. Beware that the
      provided target_datetime is UTC.
    logger: an instance of a `logging.Logger`. Information logged will be publicly available so that
      correct execution of the logger can be checked. All Exceptions will automatically be logged,
      so when something's wrong, simply raise an Exception (with an explicit text). Use
      `logger.warning` or `logger.info` for information that can useful to check if the parser is
      working correctly.

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
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
    
