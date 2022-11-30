import json
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

DEMAND_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=demandactual&region=ROI&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
DEMAND_FORECAST_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=demandforecast&region=ROI&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
WIND_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=windactual&region=ROI&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
WIND_FORECAST_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=windforecast&region=ROI&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
EXCHANGE_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=interconnection&region=ROI&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"

KINDS_URL = {
    "demand":  DEMAND_URL,
    "demand_forecast":  DEMAND_FORECAST_URL,
    "wind":WIND_URL,
    "exchange":  EXCHANGE_URL,
}


def fetch_data(
    target_datetime: datetime,
    kind: str,
    session: Optional[Session] = None,
) -> dict:
    """
    Gets values and corresponding datetimes for the specified data kind in ROI.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    assert type(target_datetime) == datetime
    assert kind != ""

    r = session or Session()
    resp = r.get(
        KINDS_URL[kind].format(dt=target_datetime.strftime("%d-%b-%Y"))
    )
    try:
        data = resp.json().get("Rows", {})
    except json.decoder.JSONDecodeError:
        raise ParserException(
            parser="IN_WE.py",
            message=f"{target_datetime}: {kind} data is not available",
        )
    filtered_data = [item for item in data if item["Value"] is not None]
    return filtered_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "IE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets values for wind production and estimates unknwon production as demand - wind - exchange"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime

    demand_data = fetch_data(
        target_datetime=target_datetime, kind="demand", session=session
    )
    wind_data = fetch_data(
        target_datetime=target_datetime, kind="wind", session=session
    )
    exchange_data = fetch_data(
        target_datetime=target_datetime, kind="exchange", session=session
    )
    assert len(demand_data) >0
    assert len(wind_data) >0
    assert len(exchange_data) >0

    production = []
    for item in demand_data:
        dt = item["EffectiveTime"]
        wind_dt = [item for item in wind_data if item["EffectiveTime"] == dt]
        if len(wind_dt)>0:
            wind_prod = wind_dt[0][
            "Value"
        ]
        else: wind_prod=0
        exchange_dt = [item for item in exchange_data if item["EffectiveTime"] == dt]
        if len(exchange_dt)>0:
            exchange = exchange_dt[0][
            "Value"
        ]
        else:
            exchange = 0
        data_point = {
            "zoneKey": "IE",
            "datetime": datetime.strptime(dt, "%d-%b-%Y %H:%M:%S").replace(
                tzinfo=pytz.timezone("Europe/Dublin")
            ),
            "production": {
                "unknown": item["Value"] - exchange - wind_prod,
                "wind": wind_prod,
            },
            "source": "eirgridgroup.com",
        }
        production += [data_point]
    return production


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """gets exchanges values for the East-West interconnector (GB->IE)"""
    if target_datetime is None:
        target_datetime =  arrow.utcnow().datetime

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    exchange_data = fetch_data(target_datetime=target_datetime, kind="exchange",session=session)

    assert len(exchange_data)>0
    filtered_exchanges = [item for item in exchange_data if item['FieldName']== 'INTER_EWIC']
    exchange = []
    for item in filtered_exchanges:
        data_point = {
        "netFlow": -item["Value"],
        "sortedZoneKeys": sortedZoneKeys,
        "datetime": datetime.strptime(item["EffectiveTime"], "%d-%b-%Y %H:%M:%S").replace(
                tzinfo=pytz.timezone("Europe/Dublin")
            ),
        "source": "eirgridgroup.com",
    }
        exchange +=[data_point]
    return exchange

@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "IE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """ gets consumption values for ROI """
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime

    demand_data = fetch_data(target_datetime=target_datetime, kind="demand",session=session)

    assert len(demand_data)>0

    demand = []
    for item in demand_data:
        data_point = {
        "zone_key":zone_key,
        "consumption":item["Value"],
        "datetime": datetime.strptime(item["EffectiveTime"], "%d-%b-%Y %H:%M:%S").replace(
                tzinfo=pytz.timezone("Europe/Dublin")
            ),

        "source": "eirgridgroup.com",
    }
        demand +=[data_point]
    return demand

@refetch_frequency(timedelta(days=1))
def fetch_consumption_forecast(
    zone_key: str = "IE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """ gets forecasted consumption values for ROI """
    demand_forecast_data = fetch_data(target_datetime=target_datetime, kind="demand_forecast",session=session)

    assert len(demand_forecast_data)>0

    demand_forecast = []
    for item in demand_forecast_data:
        data_point = {
        "zone_key":zone_key,
        "consumption":item["Value"],
        "datetime": datetime.strptime(item["EffectiveTime"], "%d-%b-%Y %H:%M:%S").replace(
                tzinfo=pytz.timezone("Europe/Dublin")
            ),

        "source": "eirgridgroup.com",
    }
        demand_forecast +=[data_point]
    return demand_forecast

@refetch_frequency(timedelta(days=1))
def fetch_wind_solar_forecasts(
    zone_key: str = "IE",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for forecasted wind produciton.
    """
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime

    wind_forecast_data = fetch_data(target_datetime=target_datetime, kind="wind_forecast",session=session)

    assert len(wind_forecast_data)>0

    wind_forecast = []
    for item in wind_forecast_data:
        data_point = {
        "zone_key":zone_key,
        "production":{"wind":item["Value"]},
        "datetime": datetime.strptime(item["EffectiveTime"], "%d-%b-%Y %H:%M:%S").replace(
                tzinfo=pytz.timezone("Europe/Dublin")
            ),

        "source": "eirgridgroup.com",
    }
        wind_forecast +=[data_point]
    return wind_forecast