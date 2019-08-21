#!/usr/bin/env python3

from requests import Session
from .lib.exceptions import ParserException
from .lib import web
from .lib import zonekey
from .lib import IN

from bs4 import BeautifulSoup
import requests
import urllib.parse as urlparse
import arrow
import datetime  
  
  
def get_production(zone_key, session=None):
    
    zonekey.assert_zone_key(zone_key, 'IN-KL')

    url = 'http://sldckerala.com/index.php'

    params={'id':1}
    headers = {'User-Agent': 'electricitymap.org'}   
    
    html = requests.get(url=url,params=params,headers=headers).text
    soup = BeautifulSoup(html, "lxml")

    # #Parse Datetime (SYSTEM STATISTICS)
    # match = re.search(r'\d{2}/\d{2}/\d{4}', soup.find("h1", {'class':'title'}).text)
    # kerala_datetime = arrow.get(datetime.datetime.strptime(match.group(),"%d/%m/%Y"),'Asia/Kolkata')
    
    #Pares Datetime (current datetime)
    date_dict = dict(urlparse.parse_qsl(urlparse.urlsplit(soup.find("div", attrs={'id':'div_date1'}).find('iframe')['src']).query))

    day = int(date_dict['selected_day'])
    month = int(date_dict['selected_month'][:2])
    year = int(date_dict['selected_year'])
    kerala_datetime = arrow.get(datetime.datetime(year, month, day),'Asia/Kolkata')
    
    
    
    table_body=soup.find("table", {'class':'display'})
    rows = table_body.find_all('tr')
    
    #TODO: Clean-up
    #Ref:
    #https://en.wikipedia.org/wiki/Kerala_State_Electricity_Board
    #http://www.kseb.in
    
    hydro = wind = oil = solar = 0

    for row in rows:
        cols=row.find_all('td')
        cols=[x.text.strip() for x in cols]
        #The Hydel Group 1
        if cols[0] in ['Idukki','Sabarigiri','Idamalayar','Sholayar','Pallivasal']:
            if cols[1]:
                hydro += float(cols[1])/24. *1000.
        #The Hydel Group 2
        if cols[0] in ['Kuttiadi','Panniar']:
            if cols[1]:
                hydro += float(cols[1])/24. *1000.
        #The Hydel Group 3
        if cols[0] in ['Neriamangalam','Lower Periyar','Poringalkuthu & PLBE','Sengulam','Kakkad','Kallada','Malankara']:
            if cols[1]:
                hydro += float(cols[1])/24. *1000.
        #Hydel Captive
        if cols[0] in ['Maniyar','Kuthungal']:
            if cols[1]:
                hydro += float(cols[1])/24. *1000.
        #Diesel  
        if cols[0] in ['THERMAL           BDPP',' KDPP']:
            if cols[1]:
                oil += float(cols[1])/24. *1000.  
        #Wind
        if 'WIND                  Kanjikode' in cols[0]:
            if cols[1]:
                wind += float(cols[1])/24. *1000.  
        #Solar IPPs
        if 'SOLAR' in cols[0]:
            if cols[1]:
                solar += float(cols[1])/24. *1000. 
        #Wind IPPs
        if 'Wind mills' in cols[0]:
            if cols[1]:
                wind += float(cols[1])/24. *1000.
               
    production =  {
        'biomass': 0.0,
        'coal': 0.0,
        'gas': 0.0,
        'hydro': hydro,
        'nuclear': 0.0,
        'oil': oil,
        'solar': solar,
        'wind': wind,
        'geothermal': 0.0,
        'unknown': 0.0
    }
    
    return kerala_datetime,production   
            
def get_demand(zone_key, session=None):
    
    zonekey.assert_zone_key(zone_key, 'IN-KL')

    url = 'http://sldckerala.com/index.php'

    params={'id':1}
    headers = {'User-Agent': 'electricitymap.org'}   
    
    html = requests.get(url=url,params=params,headers=headers).text
    soup = BeautifulSoup(html, "lxml")

    # #Parse Datetime (SYSTEM STATISTICS)
    # match = re.search(r'\d{2}/\d{2}/\d{4}', soup.find("h1", {'class':'title'}).text)
    # kerala_datetime = arrow.get(datetime.datetime.strptime(match.group(),"%d/%m/%Y"),'Asia/Kolkata')
    
    #Pares Datetime (current)
    date_dict = dict(urlparse.parse_qsl(urlparse.urlsplit(soup.find("div", attrs={'id':'div_date1'}).find('iframe')['src']).query))

    day = int(date_dict['selected_day'])
    month = int(date_dict['selected_month'][:2])
    year = int(date_dict['selected_year'])
    kerala_datetime = arrow.get(datetime.datetime(year, month, day),'Asia/Kolkata')
    
    table_body=soup.find("table", {'class':'display'})
    rows = table_body.find_all('tr')
    
    #TODO: Clean-up
    #Ref:
    #https://en.wikipedia.org/wiki/Kerala_State_Electricity_Board
    #http://www.kseb.in
    hydro = wind = oil = solar = 0
    for row in rows:
        cols=row.find_all('td')
        cols=[x.text.strip() for x in cols]
        #The Hydel Group 1
        if cols[0] in ['Idukki','Sabarigiri','Idamalayar','Sholayar','Pallivasal']:
            if cols[4]:
                hydro += float(cols[4])
        #The Hydel Group 2
        if cols[0] in ['Kuttiadi','Panniar']:
            if cols[4]:
                hydro += float(cols[4])
        #The Hydel Group 3
        if cols[0] in ['Neriamangalam','Lower Periyar','Poringalkuthu & PLBE','Sengulam','Kakkad','Kallada','Malankara']:
            if cols[4]:
                hydro += float(cols[4])            
        #Hydel Captive
        if cols[0] in ['Maniyar','Kuthungal']:
            if cols[4]:
                hydro += float(cols[4])
        #Diesel 
         
        if cols[0] in ['THERMAL           BDPP',' KDPP']:
            if cols[4]:
                oil += float(cols[4]) 
        #Wind
        if 'WIND                  Kanjikode' in cols[0]:
            if cols[4]:
                wind += float(cols[4])
        #Solar IPPs
        if 'SOLAR' in cols[0]:
            if cols[4]:
                solar += float(cols[4])
        #Wind IPPs
        if 'Wind mills' in cols[0]:
            if cols[4]:
                wind += float(cols[4])
               
    demand =  {
        'biomass': 0.0,
        'coal': 0.0,
        'gas': 0.0,
        'hydro': hydro,
        'nuclear': 0.0,
        'oil': oil,
        'solar': solar,
        'wind': wind,
        'geothermal': 0.0,
        'unknown': 0.0
    }
    
    return kerala_datetime,demand        
            



def fetch_consumption(zone_key='IN-KL', session=None, target_datetime=None, logger=None):
    """Fetch Karnataka consumption"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    zonekey.assert_zone_key(zone_key, 'IN-KL')

    kerala_datetime, demand = get_demand(zone_key)

    data = {
        'zoneKey': zone_key,
        'datetime': kerala_datetime.datetime,
        'consumption': demand,
        'source': 'sldckerala.com'
    }

    return data




def fetch_production(zone_key='IN-KL', session=None, target_datetime=None, logger=None):
    """Fetch Karnataka  production"""
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    kerala_datetime, production = get_production(zone_key)
    


    data = {
        'zoneKey': zone_key,
        'datetime': kerala_datetime.datetime,
        'production': production,
        'storage': {
            'hydro': 0
        },
        'source': 'sldckerala.com',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print(fetch_production('IN-KL', session))
    print(fetch_consumption('IN-KL', session))
