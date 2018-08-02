#!/usr/bin/env python3

import logging
import datetime
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

import occtonet

def fetch_production(zone_key='JP-KY', session=None,target_datetime=None,
                     logger: logging.Logger = logging.getLogger(__name__)):
    
    zone_key = 'JP-KY'
    data = {
      'zoneKey': zone_key,
      'datetime': None,
      'production': {
          'biomass': 0,
          'coal': 0,
          'gas': 0,
          'hydro': None,
          'nuclear': None,
          'oil': 0,
          'solar': None,
          'wind': None,
          'geothermal': None,
          'unknown': 0
      },
      'storage': {},
      'source': 'www.kyuden.co.jp'
    }
    # url for consumption and solar
    url = 'https://www.kyuden.co.jp/power_usages/pc.html'

    r = requests.get(url)
    r.encoding = 'utf-8'
    html = r.text 
    soup = BeautifulSoup(html, "lxml")

    # time stamp
    ts = soup.find("p", class_="puProgressNow__time").get_text()
    hours = re.findall('[\d]+(?=時)', ts)[0]
    minutes = re.findall('(?<=時)[\d]+(?=分)',ts)[0]
    # date stamp
    ds = soup.find("div", class_="puChangeGraph")
    date = re.findall('(?<=chart/chart)[\d]+(?=.gif)',str(ds))[0]

    # parse datetime
    dt = ''.join([date[:4], '-', date[4:6],'-',date[6:], ' ', 
                 "{0:02d}:{1:02d}".format(int(hours), int(minutes))])
    dt = arrow.get(dt).replace(tzinfo='Asia/Tokyo').datetime
    
    data['datetime'] = dt
    
    # consumption
    cons = soup.find("p", class_="puProgressNow__useAmount").get_text()
    cons = re.findall('(?<=使用量\xa0)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?(?=万kW／)', cons)
    cons = cons[0].replace(',','')
    # convert from 万kW to MW
    cons = float(cons)*10
    # solar
    solar = soup.find("td", class_="puProgressSun__num").get_text()
    # convert from 万kW to MW
    solar = float(solar)*10
    data['production']['solar'] = solar
   
    # add nuclear
    # Sendai and Genkai
    url_s = 'http://www.kyuden.co.jp/php/nuclear/sendai/rename.php?A=s_power.fdat&B=ncp_state.fdat&_=1520532401043'
    url_g = 'http://www.kyuden.co.jp/php/nuclear/genkai/rename.php?A=g_power.fdat&B=ncp_state.fdat&_=1520532904073'

    sendai = requests.get(url_s).text
    sendai = re.findall('(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?(?=&)', sendai)
    genkai = requests.get(url_g).text
    genkai = re.findall('(?<=gouki=)[-+]?[.]?[\d]+(?:,\d\d\d)*[\.]?\d*(?:[eE][-+]?\d+)?(?=&)', genkai)

    nuclear = 0
    if len(sendai) > 0:
        for i in range(len(sendai)):
            nuclear = nuclear + float(sendai[i])
    if len(genkai) > 0:
        for i in range(len(genkai)):
            nuclear = nuclear + float(genkai[i])
    # convert from 万kW to MW
    nuclear = nuclear*10;
    
    data['production']['nuclear'] = nuclear
    
     # add the exchange JP-CG->JP-KY
    exch_list = occtonet.fetch_exchange('JP-KY', 'JP-CG')
    # find the exchange timestamp that agrees with the consumption one
    exch_newer = True
    ind = 0
    while exch_newer:
        ind = ind - 1
        exch_newer = (exch_list[ind]['datetime']>dt)
    
    exch = -1*exch_list[ind]['netFlow']

    generation = cons + exch
    

    data['production']['unknown'] = generation-nuclear-solar
    
    return data
