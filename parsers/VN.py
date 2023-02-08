#!/usr/bin/env python3
# WORK-IN-PROGRESS for parsing price + load data of VIETNAM

import requests
import arrow
import logging
from datetime import datetime, timedelta


dt_day = arrow.now(tz='Asia/Ho_Chi_Minh').format('DD/MM/YYYY')
dt_now = arrow.now(tz='Asia/Ho_Chi_Minh').format('DD/MM/YYYY HH:mm:ss')
print('Fetching price and load data for:', dt_day, "at", dt_now, "local Vietnamese time.")

## Vietnamese National Load Dispatch Center https://www.nldc.evn.vn/
price_url="https://www.nldc.evn.vn/GiaBienHandle.ashx?d=31/01/2023"
load_url="https://www.nldc.evn.vn/PhuTaiHandle.ashx?d=31/01/2023"

##fetch_price()
# [0] = price of Northern price zone
# [1] = price of Central price zone
# [2] = price of Southern price zone

price_response = requests.get(price_url)
price_data = price_response.json()


price_north = price_data['data'][0]
price_central = price_data['data'][1]
price_south = price_data['data'][2]

for hours in range(len(price_north)):
    price_values = dict(hour=datetime.time(datetime.strptime(("%d:%02d" % (int(hours/2), (hours*30 % 60))), "%H:%M")),
                       north=price_north[hours],
                       central=price_central[hours],
                       south=price_south[hours])
    print("PRICE:",
          price_values)

print("Latest timestamp")
print(price_values['hour'])

##fetch_consumption()
# [0] = load of Northern Vietnam
# [1] = load of Central Vietnam
# [2] = load of Southern Vietnam
# [3] = load of Vietnam (total)

load_response = requests.get(load_url)
load_data = load_response.json()

load_north = load_data['data'][0]
load_central = load_data['data'][1]
load_south = load_data['data'][2]
load_vietnam = load_data['data'][3]

for hours in range(len(load_vietnam)):
    load_values = dict(hour=datetime.time(datetime.strptime(("%d:%02d" % (int(hours/2), (hours*30 % 60))), "%H:%M")),
                       north_load=load_north[hours],
                       central_load=load_central[hours],
                       south_load=load_south[hours],
                       vietnam_load=load_vietnam[hours]
    )

    print("LOAD:",
          load_values)


a = dict(datetime=load_values['hour'],
         consumption=load_values['north_load'],
         zone_key="VN-N")
print('Latest entry for loead in VN-N:')
print(a)

##just for testing
#print("RAW PRICE DATA:", price_data)
#print("RAW LOAD DATA:", load_data)
