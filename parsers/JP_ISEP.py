#!/usr/bin/env python3
import os
import time
import arrow
import logging
import datetime
import pyvirtualdisplay
import selenium.webdriver

import pandas as pd

from glob import glob
from selenium.webdriver.firefox.options import Options

url = 'https://isep-energychart.com/en/graphics/electricityproduction/?region={region}&period_year={year}&period_month={month}&period_day={day}&period_length=1day&display_format=residual_demand'
timezone = 'Japan'

MAP_ZONE_TO_REGION_NAME = {
    'JP': 'all',
    'JP-HKD': 'hokkaido',
    'JP-TH': 'tohoku',
    'JP-TK': 'tokyo',
    'JP-CB': 'chubu',
    'JP-HR': 'hokuriku',
    'JP-KN': 'kansai',
    'JP-CG': 'chugoku',
    'JP-SK': 'shikoku',
    'JP-KY': 'kyushu',
    'JP-ON': 'okinawa'
}

COLUMN_MAP = {
   'Area Demand Electricity Generation[MWh]':'consumption',
   'Geothermal Electricity Generation[MWh]':'geothermal',
   'Biomass Electricity Generation[MWh]':'biomass',
   'Hydro Electricity Generation[MWh]':'hydro', 
   'Wind Electricity Generation[MWh]':'wind',
   'Solar PV Electricity Generation[MWh]':'solar',
   'Nuclear Electricity Generation[MWh]':'nuclear',
   'Fossil Fuels Electricity Generation[MWh]':'unknown',
   'Pumped Hydro Electricity Generation[MWh]':'pumped hydro',
   'Interconnection Electricity Generation[MWh]':'exchanges',
   'Solar PV Curtailment Electricity Generation[MWh]': 'solar curtailment',
   'Wind Curtailment Electricity Generation[MWh]': 'wind curtailment'
}

# prevents selenium from opening an actual browser window
display = pyvirtualdisplay.Display(visible=0, size=(1280, 1024,))
display.start()

def make_firefox_driver():
    fp = selenium.webdriver.FirefoxProfile()
    fp.set_preference("browser.download.dir",os.getcwd());
    fp.set_preference("browser.download.folderList",2);
    fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/octet-stream");
    
    opts = Options()
    opts.profile = fp
    
    return selenium.webdriver.Firefox(options = opts)


def get_data(region, year, month, day):
    driver = make_firefox_driver()
    driver.get(url.format(**{'region':region,'year':year,'month':month,'day':day}))

    elem = driver.find_elements_by_xpath("//*[@data-file_type='xls']")[0]
    elem.click()
    
    #Add leading 0s to month and day
    _month = '%02.0f'%month
    _day = '%02.0f'%day
    
    i = 0
    files_found = glob(f'Electricity*{region}-{year}{_month}{_day}*.xls')
    while len(files_found) == 0 and i < 10:
        time.sleep(1)
        files_found = glob(f'Electricity*{region}-{year}{_month}{_day}*.xls')
        i += 1
    driver.close()
    assert len(files_found) > 0, 'Excel file not downloaded properly'
    df = pd.read_excel(files_found[0])

    os.remove(files_found[0])
    return df

def process_data(df, year):
    #add year to datetime
    df['Date & Time'] = df['Date & Time'].map(lambda x: '%s '%year + x)
    
    #convert to timestamp with timezone info
    df['ts'] = pd.to_datetime(df['Date & Time'], format=('%Y %b %d. %H:%M'))
    df['ts'] = df['ts'].dt.tz_localize(timezone).dt.tz_convert('UTC')
    
    df = df.rename(columns = COLUMN_MAP)
    
    df['hydro storage'] = df['pumped hydro'].map(lambda x: x if x < 0 else 0)
    df['hydro discharge'] = df['pumped hydro'].map(lambda x: x if x > 0 else 0)

    #Should be removed if we ever handle curtailment data separately
    if 'wind' in df.columns:
        df['wind adjusted'] = df['wind'] + df.get('wind curtailment',0)

    if 'solar' in df.columns:
        df['solar adjusted'] = df['solar'] + df.get('solar curtailment',0)
    return df


def fetch_production(zone_key='JP', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    """Requests the historic production mix (in MW) of japan

    Arguments:
    ----------
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not
      provided, we should default it to now. If past data is not available,
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
    logger: an instance of a `logging.Logger` that will be passed by the
      backend. Information logged will be publicly available so that correct
      execution of the logger can be checked. All Exceptions will automatically
      be logged, so when something's wrong, simply raise an Exception (with an
      explicit text). Use `logger.warning` or `logger.info` for information
      that can useful to check if the parser is working correctly. A default
      logger is used so that logger output can be seen when coding / debugging.

    Returns:
    --------
    If no data can be fetched, any falsy value (None, [], False) will be
      ignored by the backend. If there is no data because the source may have
      changed or is not available, raise an Exception.

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
    if target_datetime is None:
        # This data is only available with approx 4 month delay
        raise NotImplementedError(
            'target_datetime must be provided, this parser can only parse historic data')

    
    region = MAP_ZONE_TO_REGION_NAME[zone_key]

    year = target_datetime.year
    month = target_datetime.month
    day = target_datetime.day

    df = get_data(region,year,month,day)
    df = process_data(df, year)

    data = []
    for name, row in df.iterrows():
        dat = {
            'datetime': row['ts'].to_pydatetime(),
            'zoneKey': zone_key,
            'production': {
                'biomass': row.get('biomass', None),
                'hydro': row.get('hydro', None),
                'hydro discharge': row.get('hydro discharge', None),
                'nuclear': row.get('nuclear', None),
                'solar': row.get('solar adjusted', None),
                'wind': row.get('wind adjusted', None),
                'geothermal': row.get('geothermal', None),
                'unknown': row.get('unknown', None)
            },
            'storage': {
                'hydro storage': row.get('hydro storage', None)
            },
            'source': 'isep-energychart.com'
        }
        data += [dat]

    return data


def fetch_consumption(zone_key='JP', session=None,
                     target_datetime: datetime.datetime = None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    """Requests the historic consumption mix (in MW) of japan

    Arguments:
    ----------
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not
      provided, we should default it to now. If past data is not available,
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
    logger: an instance of a `logging.Logger` that will be passed by the
      backend. Information logged will be publicly available so that correct
      execution of the logger can be checked. All Exceptions will automatically
      be logged, so when something's wrong, simply raise an Exception (with an
      explicit text). Use `logger.warning` or `logger.info` for information
      that can useful to check if the parser is working correctly. A default
      logger is used so that logger output can be seen when coding / debugging.

    Returns:
    --------
    If no data can be fetched, any falsy value (None, [], False) will be
      ignored by the backend. If there is no data because the source may have
      changed or is not available, raise an Exception.

    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'consumption': 10.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime is None:
        # This data is only available with approx 4 month delay
        raise NotImplementedError(
            'target_datetime must be provided, this parser can only parse historic data')

    
    region = MAP_ZONE_TO_REGION_NAME[zone_key]

    year = target_datetime.year
    month = target_datetime.month
    day = target_datetime.day

    df = get_data(region,year,month,day)
    df = process_data(df, year)

    data = []
    for name, row in df.iterrows():
        dat = {
            'datetime': row['ts'].to_pydatetime(),
            'zoneKey': zone_key,
            'consumption': row.get('consumption', None),
            'source': 'isep-energychart.com'
        }
        data += [dat]

    return data



if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    print('fetch_production() ->')
    print(fetch_production(target_datetime=pd.Timestamp('2019-01-01')))
    print('fetch_consumption() ->')
    print(fetch_consumption(target_datetime=pd.Timestamp('2019-01-01')))
