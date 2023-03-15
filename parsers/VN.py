# WORK-IN-PROGRESS for parsing price + load data of VIETNAM
#!/usr/bin/env python3

import requests
import arrow
import pytz

from logging import Logger, getLogger
from datetime import datetime
from requests import Session
from typing import Optional

dt_day = arrow.now(tz='Asia/Ho_Chi_Minh').format('YYYY-MM-DD')
print('Fetching all available price and load data for >', dt_day, '< in Vietnam.')
tz = pytz.timezone("Asia/Ho_Chi_Minh")

## Vietnamese National Load Dispatch Center https://www.nldc.evn.vn/
price_url="https://www.nldc.evn.vn/GiaBienHandle.ashx?d=31/01/2023"
load_url="https://www.nldc.evn.vn/PhuTaiHandle.ashx?d=31/01/2023"

zone_key_list = [['VN-N'], ['VN-C'], ['VN-S'], ['VN']]

##  fetch_price()
# [0] = price of Northern price zone
# [1] = price of Central price zone
# [2] = price of Southern price zone

price_response = requests.get(price_url)
price_data = price_response.json()


price_north = price_data['data'][0]
price_central = price_data['data'][1]
price_south = price_data['data'][2]

load_list = []
load_values = []

for hours in range(len(price_north)):
    price_values = dict(hour=datetime.time(datetime.strptime(("%d:%02d" % (int(hours/2), (hours*30 % 60))), "%H:%M")),
                       north=price_north[hours],
                       central=price_central[hours],
                       south=price_south[hours])
    print("PRICE:",
          price_values)

##  fetch_consumption()
# [0] = load of Northern Vietnam
# [1] = load of Central Vietnam
# [2] = load of Southern Vietnam
# [3] = load of Vietnam (total)

def fetch_consumption(
#    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):

    load_response = requests.get(load_url)
    load_data = load_response.json()

    load_north = load_data['data'][0]
    load_central = load_data['data'][1]
    load_south = load_data['data'][2]
    load_vietnam = load_data['data'][3]

    result_list = []

    for hours in range(len(load_vietnam)):
        load_values.append(
            dict(hour=datetime.combine(arrow.get(dt_day).datetime,
                                       datetime.time(datetime.strptime(("%d:%02d" % (int(hours / 2),
                                       (hours * 30 % 60))), "%H:%M")),
                                       tzinfo=tz),
                 north_load=load_north[hours], central_load=load_central[hours], south_load=load_south[hours],
                 vietnam_load=load_vietnam[hours])
        )


    for m in load_values:
        result_list.append(
            {
                "datetime": m['hour'],
                "consumption": m['north_load'],
                "zone_key": 'VN-N',
                "source": 'nldc.evn.vn'
            }
        )

    for n in load_values:
        result_list.append(
            {
                "datetime": n['hour'],
                "consumption": n['central_load'],
                "zone_key": 'VN-C',
                "source": 'nldc.evn.vn'
            }
        )

    for o in load_values:
        result_list.append(
            {
                "datetime": o['hour'],
                "consumption": o['south_load'],
                "zone_key": 'VN-S',
                "source": 'nldc.evn.vn'
            }
        )

    for p in load_values:
        result_list.append(
            {
                "datetime": p['hour'],
                "consumption": p['vietnam_load'],
                "zone_key": 'VN',
                "source": 'nldc.evn.vn'
            }
        )

    return result_list

if __name__ == "__main__":
    print("fetch_consumption() ->")
    print(fetch_consumption())
