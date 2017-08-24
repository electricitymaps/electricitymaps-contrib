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
    """Takes content from the corresponding webpage and returns the necessary outputs in a dataframe"""
    #get the response as an html
    soup = BeautifulSoup(resp.text, 'html.parser')
    #Each variable correspond to a row
    rows = soup.find_all("row")
    #Extract the name of variables and position
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
    #Define output frame
    obj = pd.DataFrame(0, index = range(24), columns = ['hour'] + variables)
    #Fill it with hours and variables' value
    obj.hour= hours
    for i_row, row in enumerate(corresponding_row):
        numbers = [float(numb.text) for numb in rows[row].find_all("number")]
        for i_num, num in enumerate(numbers):
            obj.loc[i_num,(variables[i_row])] = num
    #Define negative values to NaN
    obj[obj<0] = 0
    
    return obj


def fetch_hourly_production(country_code, obj, hour, date):          
    #output frame
    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'cndc.bo',
    }
    
    #Fill datetime variable
    data['datetime'] = arrow.get(date, 'YYYY-MM-DD').replace(tzinfo=tz_bo, hour=hour).datetime   
    #Datetime are recorded from hour 1 to 24 in the web service
    if hour == 0:
        hour = 24
    #Fill production types
    for i_type in MAP_GENERATION.keys(): 
        data['production'][i_type] = obj[MAP_GENERATION[i_type]][obj.hour == hour].iloc[0]
    
    return data


def fetch_production(country_code='BO', session=None):
    #Define actual and last day (for midnight data)
    now = arrow.now(tz=tz_bo)
    formatted_date = now.format('YYYY-MM-DD')
    past_formatted_date = arrow.get(formatted_date, 'YYYY-MM-DD').shift(days=-1).format('YYYY-MM-DD')

    #Define output frame
    actual_hour = now.hour
    data = [dict() for h in range(actual_hour+1)]
    
    #initial path for url to request
    url_init = 'http://www.cndc.bo/media/archivos/graf/gene_hora/despacho_diario.php?fechag=' 

    #Start with data for midnight
    url = url_init + past_formatted_date
    #Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = webparser(response)
    data_temp = fetch_hourly_production(country_code, obj, 0, formatted_date)
    data[0] = data_temp
    
    #Fill data for the other hours until actual hour
    if actual_hour>1:
        url = url_init + formatted_date
        #Request and rearange in DF
        r = session or requests.session()
        response = r.get(url)
        obj = webparser(response)
        for h in range(1, actual_hour+1):
            data_temp = fetch_hourly_production(country_code, obj, h, formatted_date)
            data[h] = data_temp

    return data
    

def fetch_hourly_generation_forecast(country_code, obj, hour, date):
    #output frame
    data = {
        'countryCode': country_code,
        'value': {},
        'source': 'cndc.bo',
    }
    
    #Fill forecasted value
    data['value'] = obj['Gen.Prevista'][obj.hour == hour].iloc[0]
    
    #Fill datetime variable - changing format if midnight (datetime are recorded from hour 1 to 24 in the webservice)
    if hour == 24:
        hour = 0
        date = arrow.get(date, 'YYYY-MM-DD').shift(days=+1).format('YYYY-MM-DD')
    data['datetime'] = arrow.get(date, 'YYYY-MM-DD').replace(tzinfo=tz_bo, hour=hour).datetime   
    
    return data


def fetch_generation_forecast(country_code = 'BO', session=None):
    #Define actual and last day (for midnight data)
    formatted_date = arrow.now(tz=tz_bo).format('YYYY-MM-DD')
    
    #Define output frame
    data = [dict() for h in range(24)]

    #initial path for url to request
    url_init = 'http://www.cndc.bo/media/archivos/graf/gene_hora/despacho_diario.php?fechag=' 
    url = url_init + formatted_date
    
    #Request and rearange in DF
    r = session or requests.session()
    response = r.get(url)
    obj = webparser(response)
    
    for h in range(1,25):
        data_temp = fetch_hourly_generation_forecast('BO', obj, h, formatted_date)
        data[h-1] = data_temp

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print 'fetch_production() ->'
    print fetch_production()
    print 'fetch_generation_forecast() ->'
    print fetch_generation_forecast()
