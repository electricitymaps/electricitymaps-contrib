#!/usr/bin/env python3

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# The numpy and pandas libraries are used to manipulate real time data
import pandas as pd
# The BeautifulSoup library is used parse web html
from bs4 import BeautifulSoup

tz_bo = 'America/La_Paz'

MAP_GENERATION = {
    'hydro': 'Hidro',
    'unknown': 'Termo',
    'wind': 'Intermitentes'
}


def webparser(resp):
    """
    Takes content from the corresponding webpage and returns the necessary outputs in a dataframe
    """
    # get the response as an html
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Each variable correspond to a row
    rows = soup.find_all("row")
    # Extract the name of variables and position
    variables = []
    corresponding_row = []
    hours = []
    for i_row in range(len(rows)):
        for tag in rows[i_row].find_all("string"):
            if not tag.get_text().isdigit():
                variables.append(tag.get_text().strip())
                corresponding_row.append(i_row)
            else:
                hours.append(int(tag.get_text()))
    # Define output frame
    obj = pd.DataFrame(0, index=range(24), columns=['hour'] + variables)
    # Fill it with hours and variables' value
    obj.hour = hours
    for i_row, row in enumerate(corresponding_row):
        numbers = [float(numb.text) for numb in rows[row].find_all("number")]
        for i_num, num in enumerate(numbers):
            obj.loc[i_num, (variables[i_row])] = num
    # Define negative values to NaN
    obj[obj < 0] = 0

    return obj


def fetch_hourly_production(zone_key, obj, date):
    """Returns a list of dictionaries."""

    production_by_hour = []
    for index, row in obj.iterrows():

        data = {
            'zoneKey': zone_key,
            'production': {},
            'storage': {},
            'source': 'cndc.bo',
        }
        # Fill datetime variable
        # Datetime are recorded from hour 1 to 24 in the web service
        if row['hour'] == 24:
            row['hour'] = 0
            date = arrow.get(date, 'YYYY-MM-DD').shift(days=+1).format('YYYY-MM-DD')
            # date = arrow.now(tz=tz_bo).format('YYYY-MM-DD')
        data['datetime'] = arrow.get(date, 'YYYY-MM-DD').replace(tzinfo=tz_bo,
                                                                 hour=int(row['hour'])).datetime

        # Fill production types
        for i_type in MAP_GENERATION.keys():
            try:
                data['production'][i_type] = row[MAP_GENERATION[i_type]]
            except KeyError as e:
                data['production'] = None
                break

        production_by_hour.append(data)

    return production_by_hour


def fetch_production(zone_key='BO', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
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

    # Define actual and previous day (for midnight data).
    now = arrow.now(tz=tz_bo)
    formatted_date = now.format('YYYY-MM-DD')
    past_formatted_date = arrow.get(formatted_date, 'YYYY-MM-DD').shift(days=-1).format(
        'YYYY-MM-DD')

    # initial path for url to request
    url_init = 'http://www.cndc.bo/media/archivos/graf/gene_hora/despacho_diario.php?fechag='

    # Start with data for previous day in order to get midnight data.
    url = url_init + past_formatted_date
    r = session or requests.session()
    response = r.get(url)
    obj = webparser(response)
    data_yesterday = fetch_hourly_production(zone_key, obj, past_formatted_date)

    # Now get data for rest of today.
    url = url_init + formatted_date
    r = session or requests.session()
    response = r.get(url)
    obj = webparser(response)
    data_today = fetch_hourly_production(zone_key, obj, formatted_date)

    data = data_yesterday + data_today

    # Drop any datapoints where;
    # 1) A type of generation is totally missing resulting in None.
    # 2) Datapoint is in the future.
    # 3) All production values are zero, this can happen because the data source
    #    updates ~5mins after the hour so condition 2 will pass.
    valid_data = []
    for datapoint in data:
        if datapoint['production'] is None:
            continue
        elif now.datetime < datapoint['datetime']:
            continue
        elif sum(datapoint['production'].values()) == 0.0:
            continue
        else:
            valid_data.append(datapoint)

    return valid_data


def fetch_hourly_generation_forecast(zone_key, obj, date):
    """Returns a list of dictionaries."""

    hourly_forecast = []
    for index, row in obj.iterrows():
        data = {
            'zoneKey': zone_key,
            'value': {},
            'source': 'cndc.bo',
        }

        # Fill forecasted value
        data['value'] = row['Gen.Prevista']

        # Fill datetime variable - changing format if midnight (datetime are recorded from hour 1 to 24 in the webservice)
        if row['hour'] == 24:
            row['hour'] = 0
            date = arrow.get(date, 'YYYY-MM-DD').shift(days=+1).format('YYYY-MM-DD')
        data['datetime'] = arrow.get(date, 'YYYY-MM-DD').replace(tzinfo=tz_bo,
                                                                 hour=int(row['hour'])).datetime

        hourly_forecast.append(data)

    return hourly_forecast


def fetch_generation_forecast(zone_key='BO', session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    # Define actual and last day (for midnight data)
    formatted_date = arrow.now(tz=tz_bo).format('YYYY-MM-DD')

    # initial path for url to request
    url_init = 'http://www.cndc.bo/media/archivos/graf/gene_hora/despacho_diario.php?fechag='
    url = url_init + formatted_date

    r = session or requests.session()

    response = r.get(url)

    obj = webparser(response)
    forecast = fetch_hourly_generation_forecast('BO', obj, formatted_date)

    return forecast


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_generation_forecast() ->')
    print(fetch_generation_forecast())
