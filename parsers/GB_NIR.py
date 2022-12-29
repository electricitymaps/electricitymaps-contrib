"""
Parser for Northern Ireland, uses the SONI / EirGrid SmartGrid dashboard. The
following data types are available:

Consumption
Production
Exchanges GB->GB-NIR and GB-NIR->IE
"""

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

from dateutil import tz
from requests import ConnectionError, Response, Session

from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

TZ = "Europe/Dublin"


def _parse_effective_time(time_str: str):
    """
    Parses the EffectiveTime timestamps (e.g. 27-Dec-2022 00:00:00) from
    SmartGrid dashboard into TZ-aware datetime objects.
    """
    naive_dt = datetime.strptime(time_str, "%d-%b-%Y %H:%M:%S")
    return naive_dt.replace(tzinfo=tz.gettz(name=TZ))


def _fetch_json_data(
    region: str,
    dataset: str,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
) -> dict:
    """
    Fetches the requested json records for the specified date between 00:00 and
    23:59 from the SmartGrid monitor.

    Parameters:
        region: name of the region, options "NI", "ROI" or "ALL".

        dataset: name of the dataset, e.g. demandactual, interconnection etc.
        Examine the SmartGrid dashboard for available options.

    Returns:
        The fetched rows of data as a list of dictionaries.
    """
    DATA_URL = "https://www.smartgriddashboard.com/DashboardService.svc/data"

    if target_datetime is None:
        date_to = datetime.now(tz.gettz(name=TZ))
    else:
        date_to = target_datetime.astimezone(tz.gettz(name=TZ))
    # get all available data for the last 48 hours
    date_from = date_to - timedelta(days=2)

        params = {
            "area": dataset,
            "region": region,
            "datefrom": date_from,
            "dateto": date_to,
        }
    try:
        response: Response = session.get(DATA_URL, params=params)
        return response.json()["Rows"]
    except ConnectionError as e:
        ParserException("GB_NIR.py", f"Failed to connect to SmartGrid Dashboard: {e}")
        raise ConnectionError


@refetch_frequency(timedelta(minutes=15))
def fetch_consumption(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    try:
        demand_json = _fetch_json_data("NI", "demandactual", session, target_datetime)
        consumption_list = []

        for row in demand_json:
            if row["Value"]:
                consumption_list.append(
                    {
                        "zoneKey": zone_key,
                        "datetime": _parse_effective_time(row["EffectiveTime"]),
                        "consumption": float(row["Value"]),
                        "source": "smartgriddashboard.com",
                    }
                )
            else:
                return consumption_list

        return consumption_list
    except TypeError as e:
        ParserException(
            "GB_NIR.py", f"Failed to retrieve consumption at requested timestamp: {e}"
        )
        raise TypeError


@refetch_frequency(timedelta(minutes=15))
def fetch_production(
    zone_key: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """
    Fetches the exchange information for either the GB->GB-NIR (by default) or
    GB-NIR->IE interconnections. All values are in MW.

    GB->GB-NIR data is retrieved directly from the SmartGrid monitor based on
    the available data for the Moyle interconnector between NI and Scotland.

    GB-NIR->IE data is computed based on the available data from the NI grid
    with the following formula:

        production_NI + moyle_powerflows_to_NI - demand_NI

    where production_NI is the total electricity production in Northern Ireland,
    demand_NI is the demand and moyle_powerflows_to_NI describes the power flow
    from the Scottish grid.
    """
    try:
        generation_json = _fetch_json_data(
            "NI", "generationactual", session, target_datetime
        )
        wind_json = _fetch_json_data("NI", "windactual", session, target_datetime)

        production_list = []

        for generation_row, wind_row in zip(generation_json, wind_json):
            if generation_row["Value"] and wind_row["Value"]:
                total_generation_mw = float(generation_row["Value"])
                wind_generation_mw = float(wind_row["Value"])

                unknown_generation_mw = (
                    total_generation_mw - wind_generation_mw
                )  # remaining generation

                production_list.append(
                    {
                        "zoneKey": zone_key,
                        "datetime": _parse_effective_time(
                            generation_row["EffectiveTime"]
                        ),
                        "production": {
                            "biomass": None,
                            "coal": None,
                            "gas": None,
                            "hydro": None,
                            "nuclear": None,
                            "oil": None,
                            "solar": None,
                            "wind": wind_generation_mw,
                            "geothermal": None,
                            "unknown": unknown_generation_mw,
                        },
                        "source": "smartgriddashboard.com",
                    }
                )
            else:
                return production_list

        return production_list

    except TypeError as e:
        ParserException(
            "GB_NIR.py", f"Failed to retrieve production at requested timestamp: {e}"
        )
        raise TypeError


@refetch_frequency(timedelta(minutes=15))
def fetch_exchange(
    zone_key1: str = "GB",
    zone_key2: str = "GB-NIR",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    moyle_json = _fetch_json_data("NI", "interconnection", session, target_datetime)

    interconnection_list = []

    if sortedZoneKeys == "GB->GB-NIR":
        for moyle_row in moyle_json:
            if moyle_row["Value"]:
                interconnection_list.append(
                    {
                        "sortedZoneKeys": sortedZoneKeys,
                        "datetime": _parse_effective_time(moyle_row["EffectiveTime"]),
                        "netFlow": moyle_row["Value"],
                        "source": "smartgriddashboard.com",
                    }
                )
            else:
                return interconnection_list

    elif sortedZoneKeys == "GB-NIR->IE":
        production_json = _fetch_json_data(
            "NI", "generationactual", session, target_datetime
        )

        demand_json = _fetch_json_data("NI", "demandactual", session, target_datetime)

        for production_row, demand_row, moyle_row in zip(
            production_json, demand_json, moyle_json
        ):
            production_mw = production_row["Value"]
            demand_mw = demand_row["Value"]
            moyle_mw = moyle_row["Value"]

            if production_mw and demand_mw and moyle_mw:
                power_flow_mw = (
                    production_mw + moyle_mw - demand_mw
                )  # power flow gb_nir -> ie
                interconnection_list.append(
                    {
                        "sortedZoneKeys": sortedZoneKeys,
                        "datetime": _parse_effective_time(moyle_row["EffectiveTime"]),
                        "netFlow": power_flow_mw,
                        "source": "smartgriddashboard.com",
                    }
                )
            else:
                return interconnection_list

        return interconnection_list


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange(GB, GB-NIR)")
    print(fetch_exchange("GB", "GB-NIR"))
    print("fetch_exchange(GB-NIR, IE)")
    print(fetch_exchange("GB-NIR", "GB-IE"))
