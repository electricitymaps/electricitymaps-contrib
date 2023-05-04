import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pandasql as psql
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

"""
This module is used to read the exchange values on a hourly basis for a day from India West to North, East, South. 
This module also calculates the total electricity consumption by India West.
The data is fetched from https://www.wrldc.in using APIs which provide data in JSON format
India West constitutes of Gujrat, Madhya Pradesh, Chattishgarh, Maharashtra, Goa, DD, DNH

These APIs return the data from midnight 12:00am to current time at which the parser is run  
"""

IN_WE_PROXY = "https://in-proxy-jfnx5klx2a-el.a.run.app"


""" 
Exchange data parser
source: https://www.wrldc.in/content/166_1_FlowsonInterRegionalLinks.aspx
sample data:
[{
    "Region_Id": 2,
    "Region_Name": "WR-ER",
    "Export_Ttc": 25000.0,
    "Import_Ttc": 25000.0,
    "Long_Term": 955.0,
    "Short_Term": -125.0,
    "Px_Import": 35.0,
    "Px_Export": 0.0,
    "Total": 322.0,
    "Current_Loading": -1052.0,
    "lastUpdate": "2023-04-05 12:24:09 PM"
  },
  {
    "Region_Id": 3,
    "Region_Name": "WR-NR",
    "Export_Ttc": 17800.0,
    "Import_Ttc": 4000.0,
    "Long_Term": -1418.0,
    "Short_Term": -600.0,
    "Px_Import": 2230.0,
    "Px_Export": 0.0,
    "Total": -1266.0,
    "Current_Loading": -363.0,
    "lastUpdate": "2023-04-05 12:24:09 PM"
  }
]
"""


EXCHANGE_URL = (
    f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Region_Wise?"
    f"host=https://www.wrldc.in"
)

EXCHANGES_ZONE_DATA_MAPPING = {
    "IN-SO->IN-WE": "WR-SR",
    "IN-EA->IN-WE": "WR-ER",
    "IN-NO->IN-WE": "WR-NR",
}

EXCHANGE_DATETIME_COLUMN_NAME = "lastUpdate"

# For each hour, get the average of current loading value for a given exchange like IN_SO->IN_WE
EXCHANGE_SQL_QUERY = """
    select 
    strftime ('%Y-%m-%d %H:00:00',lastUpdate) as last_update_hour, 
    -round(avg(Current_Loading), 3) as exchange_value 
    from dataframe 
    where Region_Name = '{zone_id}' 
    group by last_update_hour
    order by last_update_hour
    """


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """This method is called by IN-EA, IN-SO, IN-NO zone's parsers to get the exchange data with IN-WA zone.
    This is the entrypoint to this module for the parsers to fetch Extensions"""

    exchange_zone_key, zone_key_matching_source_data = get_exchange_zone_key(
        zone_key1, zone_key2
    )

    if target_datetime is None:
        target_datetime = arrow.now().datetime

    dataframe = get_dataframe_from_exchange_url(
        EXCHANGE_URL, EXCHANGE_DATETIME_COLUMN_NAME, target_datetime, session
    )
    result = psql.sqldf(
        EXCHANGE_SQL_QUERY.format(zone_id=zone_key_matching_source_data), locals()
    )
    exchanges = convert_result_to_exchanges(exchange_zone_key, result)
    return exchanges


def convert_result_to_exchanges(exchange_zone_key, result):
    return [
        {
            "netFlow": result["exchange_value"][index],
            "sortedZoneKeys": exchange_zone_key,
            "datetime": pd.Timestamp(
                result["last_update_hour"][index], tz="Asia/Kolkata"
            ).to_pydatetime(),
            "source": "wrldc.in",
        }
        for index in result.index
    ]


def get_exchange_zone_key(zone_key1, zone_key2):
    exchange_zone_key = "->".join(sorted([zone_key1, zone_key2]))
    if exchange_zone_key not in EXCHANGES_ZONE_DATA_MAPPING.keys():
        raise ParserException("IN_WE_new.py", "Invalid zone queried from the source")

    return exchange_zone_key, EXCHANGES_ZONE_DATA_MAPPING[exchange_zone_key]


""" 
Consumption data parser 
source: https://www.wrldc.in/content/164_1_StateScheduleVsActual.aspx 
sample data:
[{
    "stateid": 0,
    "StateName": "Gujrat",
    "Sch_Drawal": 8470.0,
    "Act_Drawal": 8651.0,
    "current_datetime": "2023-04-05 09:02:09",
    "Frequency": 50.13,
    "Deviation": 181.0,
    "Generation": 8518.0,
    "Demand": 17169.0,
    "Act_Data": 0.0,
    "Sch_Data": 0.0
  },
  {
    "stateid": 0,
    "StateName": "Madhya Pradesh",
    "Sch_Drawal": 4360.0,
    "Act_Drawal": 4280.0,
    "current_datetime": "2023-04-05 09:02:09",
    "Frequency": 50.13,
    "Deviation": -80.0,
    "Generation": 4138.0,
    "Demand": 8418.0,
    "Act_Data": 0.0,
    "Sch_Data": 0.0
  }
]
    
"""


CONSUMPTION_URL = (
    f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData_state_Wise?"
    f"host=https://www.wrldc.in"
)
# For each hour and state, get the average consumption and then add the values across the states to get the Total
# consumption in West on a per-hour basis
CONSUMPTION_SQL_QUERY = """
    select state_data.last_update_hour as last_update_hour, 
    sum(state_data.consumption_value) as consumption_value
    from 
    (
        select
        StateName as state, 
        strftime('%Y-%m-%d %H:00:00',current_datetime) as last_update_hour, 
        round(avg(Act_Drawal), 3) as consumption_value 
        from dataframe 
        group by StateName, last_update_hour
        order by StateName, last_update_hour
    ) AS state_data
    group by state_data.last_update_hour
    order by state_data.last_update_hour
    """
CONSUMPTION_DATETIME_COLUMN_NAME = "current_datetime"


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "IN-WE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    if target_datetime is None:
        target_datetime = arrow.now().datetime

    dataframe = get_dataframe_from_exchange_url(
        CONSUMPTION_URL, CONSUMPTION_DATETIME_COLUMN_NAME, target_datetime, session
    )
    result = psql.sqldf(CONSUMPTION_SQL_QUERY, locals())
    exchanges = convert_result_to_consumption(zone_key, result)
    return exchanges


def convert_result_to_consumption(zone_key, result):
    return [
        {
            "zoneKey": zone_key,
            "datetime": pd.Timestamp(
                result["last_update_hour"][index], tz="Asia/Kolkata"
            ).to_pydatetime(),
            "consumption": result["consumption_value"][index],
            "source": "wrldc.in",
        }
        for index in result.index
    ]


""" Utility methods for the data parser """


def get_dataframe_from_exchange_url(
    url: str,
    datetime_column_name: str,
    target_datetime: datetime,
    session: Optional[Session] = None,
) -> pd.DataFrame:
    """
    Given a URL and a timestamp, this method reads the JSON from the source, adds missing AM/PM in the timestamp field
    and then reads the corrected JSON as @DataFrame with correct timestamp
    """
    s = session or Session()
    payload = {"date": target_datetime.strftime("%Y-%m-%d"), "Flag": "24"}

    resp: Response = s.post(url=url, json=payload)
    data = json.loads(resp.json().get("d", {}))
    fix_timestamp_for_data(data, datetime_column_name)

    dataframe = pd.json_normalize(data)
    dataframe[datetime_column_name] = pd.to_datetime(
        dataframe[datetime_column_name], format="%Y-%d-%m %I:%M:%S %p"
    )

    return dataframe


def fix_timestamp_for_data(data, timestamp_column_name):
    """
    The data that is received from the API for both Exchange and Consumption has date fields in 12-hour format with
    missing information about 'AM/PM'. It looks like that 12-hour datetime format was used and for some reason AM/PM was
     simply truncated

    | 12 hr format datetime | 24 hr format datetime | Current datetime format |
    |-----------------------|-----------------------|-------------------------|
    | 2023-05-03 7:30 PM    | 2023-05-03 19:30      | 2023-05-03 7:30         |
    | 2023-05-03 7:30 AM    | 2023-05-03 7:30       | 2023-05-03 7:30         |
    | 2023-05-03 12:10 AM   | 2023-05-03 00:10      | 2023-05-03 12:10        |
    | 2023-05-03 12:10 PM   | 2023-05-03 12:10      | 2023-05-03 12:10        |

    It is clear that without fixing the data, we will simply aggregate data for same hour in AM and PM

    Fortunately, the data points in the JSON is ordered by timestamp
    start-> 12am, 1am, 2am ....12pm...3pm...current time <-end
    This method takes advantage of the fact that the data is ordered and iterates over the records from the beginning
    and sets the correct suffix (AM or PM) as it reads through the list and sees data for every hour sequentially
    """

    suffix = "AM"
    flipped = True
    for d in data:
        hour = datetime.strptime(d[timestamp_column_name], "%Y-%m-%d %H:%M:%S").hour
        if hour == 1:
            flipped = False

        if not flipped and hour == 12:
            if suffix == "AM":
                suffix = "PM"
            else:
                suffix = "AM"
            flipped = True

        d[timestamp_column_name] = d[timestamp_column_name] + " " + suffix
