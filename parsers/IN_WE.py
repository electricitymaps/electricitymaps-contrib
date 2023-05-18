import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any, Dict, List, Optional

import arrow
import pandas as pd
import pandasql as psql
from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib import web
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
IN_TZ = "Asia/Kolkata"

""" 
Exchange data parser
source: https://www.wrldc.in/content/166_1_FlowsonInterRegionalLinks.aspx
API : https://www.wrldc.in/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Data
sample data:
[{
    "Region_Id": 2,
    "Region_Name": "WR-ER", #Western Region -> Eastern Region
    "Export_Ttc": 25000.0,  #Export Total Transfer Capability
    "Import_Ttc": 25000.0,  #Import Total Transfer Capability
    "Long_Term": 955.0,
    "Short_Term": -125.0,
    "Px_Import": 35.0,      #Power Exchange Import
    "Px_Export": 0.0,       #Power Exchange Export
    "Total": 322.0,
    "Current_Loading": -1052.0,
    "lastUpdate": "2023-05-04 00:24:09"
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
    "lastUpdate": "2023-05-04 00:24:09"
  }
]
"""


EXCHANGE_URL = (
    f"{IN_WE_PROXY}/InterRegionalLinks_Data.aspx/Get_InterRegionalLinks_Data?"
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
) -> List[Dict[str, Any]]:
    """This method is called by IN-EA, IN-SO, IN-NO zone's parsers to get the exchange data with IN-WA zone.
    This is the entrypoint to this module for the parsers to fetch Extensions"""

    exchange_zone_key, zone_key_matching_source_data = get_exchange_zone_key(
        zone_key1, zone_key2
    )

    if target_datetime is None:
        target_datetime = arrow.now().datetime

    dataframe = get_dataframe_from_url(
        exchange_zone_key,
        EXCHANGE_URL,
        EXCHANGE_DATETIME_COLUMN_NAME,
        target_datetime,
        session,
    )
    if dataframe is None:
        return []
    result = psql.sqldf(
        EXCHANGE_SQL_QUERY.format(zone_id=zone_key_matching_source_data), locals()
    )
    exchanges = convert_result_to_exchanges(exchange_zone_key, result, logger)
    return exchanges


def convert_result_to_exchanges(exchange_zone_key, result, logger):
    exchange_list = ExchangeList(logger)

    for index in result.index:
        exchange_list.append(
            netFlow=result["exchange_value"][index],
            zoneKey=ZoneKey(exchange_zone_key),
            datetime=pd.Timestamp(
                result["last_update_hour"][index], tz=IN_TZ
            ).to_pydatetime(),
            source="wrldc.in",
        )

    return exchange_list.to_list()


def get_exchange_zone_key(zone_key1, zone_key2):
    exchange_zone_key = "->".join(sorted([zone_key1, zone_key2]))
    if exchange_zone_key not in EXCHANGES_ZONE_DATA_MAPPING.keys():
        raise ParserException("IN_WE.py", "Invalid zone queried from the source")

    return exchange_zone_key, EXCHANGES_ZONE_DATA_MAPPING[exchange_zone_key]


""" 
Consumption data parser 
source: https://www.wrldc.in/content/164_1_StateScheduleVsActual.aspx
API: https://www.wrldc.in/OnlinestateTest1.aspx/GetRealTimeData
sample data:
[{
    "stateid": 0,
    "StateName": "Gujrat",
    "Sch_Drawal": 8470.0,
    "Act_Drawal": 8651.0, #"actual drawal" in a time-block means electricity drawn by a buyer, as the case maybe, 
                          #measured by the interface meters; 
    "current_datetime": "2023-05-04 09:02:09",
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
    "current_datetime": "2023-05-04 09:02:09",
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
    f"{IN_WE_PROXY}/OnlinestateTest1.aspx/GetRealTimeData?host=https://www.wrldc.in"
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
        round(avg(Demand), 3) as consumption_value 
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
    zone_key: ZoneKey = ZoneKey("IN-WE"),
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[Dict[str, Any]]:
    if target_datetime is None:
        target_datetime = arrow.now().datetime

    dataframe = get_dataframe_from_url(
        zone_key,
        CONSUMPTION_URL,
        CONSUMPTION_DATETIME_COLUMN_NAME,
        target_datetime,
        session,
    )
    if dataframe is None:
        return []

    result = psql.sqldf(CONSUMPTION_SQL_QUERY, locals())
    consumptions = convert_result_to_consumption(zone_key, result, logger)
    return consumptions


def convert_result_to_consumption(zone_key, result, logger):
    consumption_list = TotalConsumptionList(logger)

    for index in result.index:
        consumption_list.append(
            zoneKey=zone_key,
            datetime=pd.Timestamp(
                result["last_update_hour"][index], tz=IN_TZ
            ).to_pydatetime(),
            consumption=result["consumption_value"][index],
            source="wrldc.in",
        )

    return consumption_list.to_list()


""" Utility methods for the data parser """


def get_dataframe_from_url(
    zone_key: str,
    url: str,
    datetime_column_name: str,
    target_datetime: datetime,
    session: Optional[Session] = None,
):
    """
    Given a URL and a timestamp, this method reads the JSON from the source with timestamp in 24-hour format
    and then deserializes the JSON as @DataFrame
    """
    s = session or Session()
    payload = {"date": target_datetime.strftime("%Y-%m-%d"), "Flag": "24"}
    resp = web.post_request(zone_key=zone_key, url=url, json=payload, session=s)
    json_data = web.read_response_json(zone_key, resp)
    data = json.loads(json_data.get("d"))

    dataframe = pd.json_normalize(data)
    dataframe[datetime_column_name] = pd.to_datetime(
        dataframe[datetime_column_name], format="%Y-%m-%d %H:%M:%S"
    )

    return dataframe
