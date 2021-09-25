#!/usr/bin/env python3
import logging
import datetime
import re
import pandas as pd


# Tablib is used to parse XLSX files
import tablib
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.


def fetch_production(zone_key='XK', session=None,
        target_datetime: datetime.datetime = None,
        logger: logging.Logger = logging.getLogger(__name__)) -> list:
    """Requests the last known production mix (in MW) of a given country."""
    r = session or requests.session()
    if target_datetime is None:
        url = 'https://www.kostt.com/Content/ViewFiles/Transparency/LoadForecast/Realizimi%20ditor.xlsx'
    else:
        # WHEN HISTORICAL DATA IS NOT AVAILABLE
        raise NotImplementedError(
            'This parser is not yet able to parse past dates')

    res = r.get(url)
    assert res.status_code == 200, 'XK (Kosovo) parser: GET {} returned {}'.format(url, res.status_code)
    excel_data=pd.read_excel(url, index = False, usecols = 5, header=None)




    #getting time data
    time_date_list = excel_data.iloc[13:37, 3:4].values 
    time_list = []
    for timedate in time_date_list:
        time_date_str = str(timedate)
        time_str = time_date_str.split("(")
        unformatted_time_str = time_str[1].replace(',', '').replace(']', '').replace(')', '')
        formatted_time_str = unformatted_time_str.split(' ')
        if(int(formatted_time_str[3])<10):
            time_list.append(" 0" + formatted_time_str[3] + ":" + formatted_time_str[4] + "0")
        else:
            time_list.append(" " + formatted_time_str[3] + ":" + formatted_time_str[4] + "0")




    #getting energy production data 
    unformatted_prod_list = excel_data.iloc[13:37, 4:5].values 
    prod_list = []
    for prod in unformatted_prod_list:
        prod_str = str(prod)
        unformatted_prod_str = prod_str.replace('[', '')
        formatted_prod_str = unformatted_prod_str.split(']')
        prod_list.append(formatted_prod_str[0])


    
    
    # creating production dictionary with time and production energy
    productions = {} 
    for k in range(0,24):
        productions[time_list[k]] = prod_list[k]



    # getting date
    date = excel_data.iloc[5, 3]
    unformatted_date_str = str(date)
    formatted_date_str = unformatted_date_str.split(" ")
    date_str = formatted_date_str[0]



    data = []
    for time_str, prod in productions.items():
        timestamp = arrow.get(date_str + time_str).replace(tzinfo='Europe/Belgrade')
        timestamp = timestamp.shift(hours=-1) # shift to start of period
        if time_str == '00:00':
            # Based on the apparent discontinuity in production and the order in the spreadsheet
            # it seems that the last data-point belongs to the next day
            timestamp = timestamp.shift(days=1)
        data.append({
            'zoneKey': zone_key,
            'production': {
                'unknown': prod
            },
            'storage': {},
            'source': 'kostt.com',
            'datetime': timestamp.datetime
        })

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    for datum in fetch_production():
        print(datum)
