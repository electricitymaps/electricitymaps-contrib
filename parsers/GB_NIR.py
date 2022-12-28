from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

from dateutil import tz
from requests import ConnectionError, Response, Session

from parsers.lib.config import refetch_frequency

TZ = "Europe/Dublin"
DATA_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data"


def _get_previous_quarter(time: datetime):
    last_quarter_minute = 15 * (time.minute // 15)
    return time.replace(minute=last_quarter_minute)


def _parse_effective_time(time_str: str):
    naive_dt = datetime.strptime(time_str, "%d-%b-%Y %H:%M:%S")
    return naive_dt.replace(tzinfo=tz.gettz(name=TZ))


def _fetch_json_data(
    region: str,
    dataset: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
) -> dict:
    try:
        if not target_datetime:
            # get the previous datapoint as it's usually available
            target_datetime = datetime.now(tz.gettz(name=TZ)) - timedelta(minutes=15)

        previous_quarter = _get_previous_quarter(target_datetime)

        date = previous_quarter.strftime("%d-%b-%Y+%H:%M")

        params = {
            "area": dataset,
            "region": region,
            "datefrom": date,
            "dateto": date
        }

        response: Response = session.get(DATA_URL, params=params)

        return response.json()["Rows"][0]
    except ConnectionError as e:
        ParserException("GB_NIR.py", f"Failed to connect to SmartGrid Dashboard: {e}")
        raise ConnectionError


@refetch_frequency(timedelta(minutes=15))
def fetch_consumption(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    try:
        demand = _fetch_json_data("NI", "demandactual", session, target_datetime)
        demand_mw = float(demand["Value"])

        return {
            "zoneKey": zone_key,
            "datetime": _parse_effective_time(demand["EffectiveTime"]),
            "consumption": demand_mw,
            "source": "smartgriddashboard.com",
        }
    except TypeError as e:
        print("Failed to retrieve consumption at requested timestamp." + e)


@refetch_frequency(timedelta(minutes=15))
def fetch_production(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    try:
        production = _fetch_json_data(
            "NI", "generationactual", session, target_datetime
        )
        wind = _fetch_json_data("NI", "windactual", session, target_datetime)

        total_production_mw = float(production["Value"])
        wind_mw = float(wind["Value"])

        unknown_mw = total_production_mw - wind_mw  # remaining generation

        return {
            "zoneKey": zone_key,
            "datetime": _parse_effective_time(production["EffectiveTime"]),
            "production": {
                "biomass": None,
                "coal": None,
                "gas": None,
                "hydro": None,
                "nuclear": None,
                "oil": None,
                "solar": None,
                "wind": wind_mw,
                "geothermal": None,
                "unknown": unknown_mw,
            },
            "source": "smartgriddashboard.com",
        }

    except TypeError as e:
        print("Failed to retrieve production at requested timestamp." + e)


@refetch_frequency(timedelta(minutes=15))
def fetch_exchange(
    zone_key1: str = "GB",
    zone_key2: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    interconnection = _fetch_json_data(
        "NI", "interconnection", session, target_datetime
    )

    moyle_mw = float(interconnection["Value"])

    if sortedZoneKeys == "GB->GB-NIR":
        return {
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": _parse_effective_time(interconnection["EffectiveTime"]),
            "netFlow": moyle_mw,
            "source": "smartgriddashboard.com",
        }
    elif sortedZoneKeys == "GB-NIR->IE":
        production = _fetch_json_data(
            "NI", "generationactual", session, target_datetime
        )
        production_mw = float(production["Value"])

        demand = _fetch_json_data("NI", "demandactual", session, target_datetime)
        demand_mw = float(demand["Value"])

        power_flow_mw = demand_mw - production_mw - moyle_mw  # power flow gb_nir -> ie

        return {
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": _parse_effective_time(interconnection["EffectiveTime"]),
            "netFlow": power_flow_mw,
            "source": "smartgriddashboard.com",
        }


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(GB, GB-NIR)")
    print(fetch_exchange("GB", "GB-NIR"))
    print("fetch_exchange(GB-NIR, IE)")
    print(fetch_exchange("GB-NIR", "GB-IE"))
