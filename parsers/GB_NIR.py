from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

from dateutil import tz
from requests import ConnectionError, Response, Session

TZ = "Europe/Dublin"
DATA_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data"


def get_previous_quarter(time: datetime):
    last_quarter_minute = 15 * (time.minute // 15)
    return time.replace(minute=last_quarter_minute)


def fetch_json_data(
    region: str,
    dataset: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
) -> dict:
    try:
        if not target_datetime:
            target_datetime = datetime.now(tz.gettz(name=TZ))

        previous_quarter = get_previous_quarter(target_datetime)

        date = previous_quarter.strftime("%d-%b-%Y+%H:%M")

        params = (
            "?area="
            + dataset
            + "&region="
            + region
            + "&datefrom="
            + date
            + "&dateto="
            + date
        )

        response: Response = session.get(DATA_URL + params)

        return response.json()["Rows"][0]
    except ConnectionError as e:
        print("Failed to connect to SmartGrid Dashboard:" + e)
        raise ConnectionError


def fetch_consumption(
    zone_key: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    try:
        demand = fetch_json_data("NI", "demandactual", session, target_datetime)
        effective_time = datetime.strptime(demand["EffectiveTime"], "%d-%b-%Y %H:%M:%S")
        demand_mw = float(demand["Value"])

        return {
            "zoneKey": zone_key,
            "datetime": effective_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "consumption": demand_mw,
            "source": "smartgriddashboard.com",
        }
    except TypeError:
        print("Failed to retrieve consumption at requested timestamp.")


def fetch_consumption(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    try:
        demand = fetch_json_data("NI", "demandactual", session, target_datetime)
        effective_time = datetime.strptime(demand["EffectiveTime"], "%d-%b-%Y %H:%M:%S")
        demand_mw = float(demand["Value"])

        return {
            "zoneKey": zone_key,
            "datetime": effective_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "consumption": demand_mw,
            "source": "smartgriddashboard.com",
        }
    except TypeError:
        print("Failed to retrieve consumption at requested timestamp.")


def fetch_production(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    try:
        production = fetch_json_data("NI", "generationactual", session, target_datetime)
        wind = fetch_json_data("NI", "windactual", session, target_datetime)

        effective_time = datetime.strptime(
            production["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
        )
        total_production_mw = float(production["Value"])
        wind_mw = float(wind["Value"])

        unknown_mw = total_production_mw - wind_mw  # remaining generation

        return {
            "zoneKey": zone_key,
            "datetime": effective_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
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

    except TypeError:
        print("Failed to retrieve production at requested timestamp.")


def fetch_exchange(
    zone_key1: str = "GB",
    zone_key2: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    interconnection = fetch_json_data("NI", "interconnection", session, target_datetime)

    effective_time = datetime.strptime(
        interconnection["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
    )
    moyle_mw = float(interconnection["Value"])

    if sortedZoneKeys == "GB->GB-NIR":
        return {
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": effective_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "netFlow": moyle_mw,
            "source": "smartgriddashboard.com",
        }
    elif sortedZoneKeys == "GB-NIR->IE":
        production = fetch_json_data("NI", "generationactual", session, target_datetime)
        production_mw = float(production["Value"])

        demand = fetch_json_data("NI", "demandactual", session, target_datetime)
        demand_mw = float(demand["Value"])

        power_flow_mw = demand_mw - production_mw - moyle_mw  # power flow gb_nir -> ie

        effective_time = datetime.strptime(
            interconnection["EffectiveTime"], "%d-%b-%Y %H:%M:%S"
        )

        return {
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": effective_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "netFlow": power_flow_mw,
            "source": "smartgriddashboard.com",
        }


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(GB, GB-ORK)")
    print(fetch_exchange("GB", "GB-ORK"))
    print("fetch_exchange(GB-NIR, IE)")
    print(fetch_exchange("GB-NIR", "GB-IE"))
