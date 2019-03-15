#!/usr/bin/env python3

"""Parser for the ERCOT area of the United States. (~85% of Texas)"""

import csv
import io
import logging
import zipfile

import arrow
import requests
from lxml import html

from parsers.lib.exceptions import ParserException

solar_realtime_directory_url = 'http://mis.ercot.com/misapp/GetReports.do?reportTypeId=13484'
wind_realtime_directory_url = 'http://mis.ercot.com/misapp/GetReports.do?reportTypeId=13071'
realtime_demand_url = 'http://www.ercot.com/content/cdr/html/real_time_system_conditions.html'
base_zip_url = 'http://mis.ercot.com/'


def get_zipped_csv_data(logger, directory_url, session=None):
    """Returns 5 minute generation data in json format."""

    s = session or requests.session()
    response = s.get(directory_url)
    if response.status_code != 200 or not response.content:
        raise ParserException('US-TX', 'Response code: {0}'.format(response.status_code))
    html_tree = html.fromstring(response.content)
    # This xpath gets the first row to contain 'csv' and then the zip link
    most_recent_csv_zip_url = base_zip_url + html_tree.xpath("//tr[td[contains(text(),'csv')]]/td/div/a/@href")[0]

    response = s.get(most_recent_csv_zip_url)
    if response.status_code != 200 or not response.content:
        raise ParserException('US-TX', 'Response code: {0}'.format(response.status_code))
    zip_file = zipfile.ZipFile(io.BytesIO(response.content))
    reader = csv.reader(io.StringIO(zip_file.read(zip_file.namelist()[0]).decode('utf-8')))
    next(reader)  # skip header
    row = next(reader)  # only get first row
    return arrow.get(arrow.get(row[0], 'MM/DD/YYYY HH:mm').datetime, 'US/Central').datetime, float(row[1])


def get_demand_data(logger, session=None):
    s = session or requests.session()
    response = s.get(realtime_demand_url)
    if response.status_code != 200 or not response.content:
        raise ParserException('US-TX', 'Response code: {0}'.format(response.status_code))
    html_tree = html.fromstring(response.content)
    demand = float(html_tree.xpath("//tr[td[contains(text(),'Actual System Demand')]]/td[2]/text()")[0])
    date_string = str(html_tree.xpath("//div[contains(@class,'schedTime')]/text()")[0]).replace("Last Updated: ", "")
    return arrow.get(arrow.get(date_string, 'MMM DD, YYYY HH:mm:ss').datetime, 'US/Central').datetime, demand


def fetch_production(zone_key='US-TX', session=None, target_datetime=None, logger=logging.getLogger(__name__)):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session
    target_datetime (optional) -- used if parser can fetch data for a specific day
    logger (optional) -- handles logging when parser is run as main
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

    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    wind_datetime, wind = get_zipped_csv_data(logger, wind_realtime_directory_url, session=session)
    solar_datetime, solar = get_zipped_csv_data(logger, solar_realtime_directory_url, session=session)

    wind_solar_timedelta = (wind_datetime - solar_datetime).total_seconds() / 60
    if abs(wind_solar_timedelta) > 4:  # in case one was grabbed before the other was posted
        if wind_solar_timedelta > 0:  # if solar came earlier, poll it again
            solar_datetime, solar = get_zipped_csv_data(logger, solar_realtime_directory_url, session=session)
        else:  # if wind came earlier poll it again
            wind_datetime, wind = get_zipped_csv_data(logger, wind_realtime_directory_url, session=session)

    data = {
        'zoneKey': zone_key,
        'datetime': wind_datetime,
        'production': {
            'solar': solar,
            'wind': wind
        },
        'storage': {},
        'source': 'ercot.com'
    }

    return data


def fetch_consumption(zone_key='US-TX', session=None, target_datetime=None,
                      logger=logging.getLogger(__name__)):
    """Gets consumption for a specified zone, returns a dictionary."""

    demand_datetime, demand = get_demand_data(logger, session=session)

    data = {
        'zoneKey': zone_key,
        'datetime': demand_datetime,
        'consumption': demand,
        'source': 'ercot.eu'
    }

    return data


if __name__ == '__main__':
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_consumption() ->')
    print(fetch_consumption())
