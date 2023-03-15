from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pytz
from requests import Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

IE_TZ = pytz.timezone("Europe/Dublin")

DEMAND_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=demandactual&region={zone}&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
DEMAND_FORECAST_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=demandforecast&region={zone}&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
WIND_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=windactual&region={zone}&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
WIND_FORECAST_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=windforecast&region={zone}&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"
EXCHANGE_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=interconnection&region={zone}&datefrom={dt}+00%3A00&dateto={dt}+23%3A59"

KINDS_URL = {
    "demand": DEMAND_URL,
    "demand_forecast": DEMAND_FORECAST_URL,
    "wind": WIND_URL,
    "wind_forecast": WIND_FORECAST_URL,
    "exchange": EXCHANGE_URL,
}

ZONE_MAPPING = {
    "IE": {"key": "ROI", "exchange": "INTER_EWIC"},
    "GB-NIR": {"key": "NI", "exchange": "INTER_MOYLE"},
}


def fetch_data(
    target_datetime: datetime,
    zone_key: str,
    kind: str,
    session: Session,
) -> list:
    """
    Gets values and corresponding datetimes for the specified data kind in ROI.
    Removes any values that are in the future or don't have a datetime associated with them.
    """
    assert type(target_datetime) == datetime
    assert kind != ""
    assert session is not None

    resp: Response = session.get(
        KINDS_URL[kind].format(
            dt=target_datetime.strftime("%d-%b-%Y"), zone=ZONE_MAPPING[zone_key]["key"]
        )
    )
    try:
        data = resp.json().get("Rows", {})
    except:
        raise ParserException(
            parser="IE.py",
            message=f"{target_datetime}: {kind} data is not available for {zone_key}",
        )
    filtered_data = [item for item in data if item["Value"] is not None]
    return filtered_data


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets values for wind production and estimates unknwon production as demand - wind - exchange"""
    if target_datetime is None:
        target_datetime = datetime.now().replace(tzinfo=IE_TZ)

    demand_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="demand",
        session=session,
    )
    wind_data = fetch_data(
        target_datetime=target_datetime, zone_key=zone_key, kind="wind", session=session
    )
    exchange_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="exchange",
        session=session,
    )
    assert len(demand_data) > 0
    assert len(wind_data) > 0
    assert len(exchange_data) > 0

    production = []
    for item in demand_data:
        dt = item["EffectiveTime"]
        wind_dt = [item for item in wind_data if item["EffectiveTime"] == dt]
        if len(wind_dt) == 1:
            wind_prod = wind_dt[0]["Value"]
        else:
            wind_prod = 0
        exchange_dt = [item for item in exchange_data if item["EffectiveTime"] == dt]
        if len(exchange_dt) == 1:
            exchange = exchange_dt[0]["Value"]
        else:
            exchange = 0
        data_point = {
            "zoneKey": zone_key,
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
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetches exchanges values for the East-West (GB->IE) and Moyle (GB->GB-NIR)
    interconnectors.
    """
    if target_datetime is None:
        target_datetime = datetime.now().replace(tzinfo=IE_TZ)

    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))

    if sortedZoneKeys == "GB-NIR->IE":
        raise ParserException(
            parser="IE.py",
            message=f"the GB-NIR_IE interconnection is unsupported.",
        )

    exchange_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key2,
        kind="exchange",
        session=session,
    )

    assert len(exchange_data) > 0
    filtered_exchanges = [
        item
        for item in exchange_data
        if item["FieldName"] == ZONE_MAPPING[zone_key2]["exchange"]
    ]
    exchange = []
    for item in filtered_exchanges:
        data_point = {
            "netFlow": item["Value"],
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": datetime.strptime(
                item["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
            ).replace(tzinfo=pytz.timezone("Europe/Dublin")),
            "source": "eirgridgroup.com",
        }
        exchange += [data_point]
    return exchange


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """gets consumption values for ROI"""
    if target_datetime is None:
        target_datetime = datetime.now().replace(tzinfo=IE_TZ)

    demand_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="demand",
        session=session,
    )

    assert len(demand_data) > 0

    demand = []
    for item in demand_data:
        data_point = {
            "zoneKey": zone_key,
            "consumption": item["Value"],
            "datetime": datetime.strptime(
                item["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
            ).replace(tzinfo=pytz.timezone("Europe/Dublin")),
            "source": "eirgridgroup.com",
        }
        demand += [data_point]
    return demand


@refetch_frequency(timedelta(days=1))
def fetch_consumption_forecast(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """gets forecasted consumption values for ROI"""

    if target_datetime is None:
        target_datetime = datetime.now().replace(tzinfo=IE_TZ)

    demand_forecast_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="demand_forecast",
        session=session,
    )

    assert len(demand_forecast_data) > 0

    demand_forecast = []
    for item in demand_forecast_data:
        data_point = {
            "zoneKey": zone_key,
            "value": item["Value"],
            "datetime": datetime.strptime(
                item["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
            ).replace(tzinfo=pytz.timezone("Europe/Dublin")),
            "source": "eirgridgroup.com",
        }
        demand_forecast += [data_point]
    return demand_forecast


@refetch_frequency(timedelta(days=1))
def fetch_wind_forecasts(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Gets values and corresponding datetimes for forecasted wind produciton.
    """
    if target_datetime is None:
        target_datetime = datetime.now().replace(tzinfo=IE_TZ)

    wind_forecast_data = fetch_data(
        target_datetime=target_datetime,
        zone_key=zone_key,
        kind="wind_forecast",
        session=session,
    )

    assert len(wind_forecast_data) > 0

    wind_forecast = []
    for item in wind_forecast_data:
        data_point = {
            "zoneKey": zone_key,
            "production": {"wind": item["Value"]},
            "datetime": datetime.strptime(
                item["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
            ).replace(tzinfo=pytz.timezone("Europe/Dublin")),
            "source": "eirgridgroup.com",
        }
        wind_forecast += [data_point]
    return wind_forecast
