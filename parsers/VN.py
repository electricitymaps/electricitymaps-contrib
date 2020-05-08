# WORK-IN-PROGRESS for parsing price + load data of VIETNAM
#!/usr/bin/env python3

import requests
import arrow
import logging
import datetime

dt_day = arrow.now(tz='Asia/Ho_Chi_Minh').format('DD/MM/YYYY')
dt_now = arrow.now(tz='Asia/Ho_Chi_Minh').format('DD/MM/YYYY HH:mm:ss')
print('Fetching price and load data for:', dt_day, "at", dt_now, "local Vietnamese time.")

## Vietnamese National Load Dispatch Center https://www.nldc.evn.vn/
price_url="https://www.nldc.evn.vn/GiaBienHandle.ashx?d=08/05/2020"
load_url="https://www.nldc.evn.vn/PhuTaiHandle.ashx?d=08/05/2020"

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
    price_values = dict(hour=hours + 1,
                       north=price_north[hours],
                       central=price_central[hours],
                       south=price_south[hours])
    print("PRICE:",
          price_values)


##fetch_consumption()
# [0] = load of Northern Vietnam
# [1] = load of Central Vietnam
# [2] = load of Southern Vietnam
# [3] = total load of Vietnam

load_response = requests.get(load_url)
load_data = load_response.json()

load_north = load_data['data'][0]
load_central = load_data['data'][1]
load_south = load_data['data'][2]
load_vietnam = load_data['data'][3]

for hours in range(len(load_vietnam)):
    load_values = {'hour': hours + 1,
                       'north': load_north[hours],
                       'central': load_central[hours],
                       'south': load_south[hours],
                       'vietnam': load_vietnam[hours]
                }

    print("LOAD:",
          load_values)

##just for testing
print("RAW PRICE DATA:", price_data)
print("RAW LOAD DATA:", load_data)
