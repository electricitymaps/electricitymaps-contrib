"""Parser for the PJM area of the United States (US-MIDA-PJM)."""

import gzip
import json
import re
from datetime import datetime, time, timedelta, timezone
from itertools import groupby
from logging import Logger, getLogger
from operator import itemgetter
from typing import Any, Literal
from zoneinfo import ZoneInfo

import demjson3 as demjson
from bs4 import BeautifulSoup
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    GridAlertList,
    LocationalMarginalPriceList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    GridAlertType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

PARSER = "US_PJM.py"
TIMEZONE = ZoneInfo("America/New_York")
ZONE_KEY = ZoneKey("US-MIDA-PJM")
# Used for production and consumption forecast data (https://dataminer2.pjm.com/list)
DATA_MINER_API_ENDPOINT = "https://api.pjm.com/api/v1/"


US_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
DATA_PATH = "api/v1"

SOURCE = "pjm.com"

ZONE_TO_PJM_INTERFACES = {
    ZoneKey("US-MIDW-MISO"): ["MISO"],  # "MISO LMP"
    # ?: ["DEOK|OVEC"],  # Ohio Valley Electric Corporation (OVEC)
    ZoneKey("US-MIDW-LGEE"): [
        "SOUTH|LGEE"
    ],  # Louisville Gas and Electric Company (LGEE)
    ZoneKey("US-TEN-TVA"): ["SOUTH|TVA"],  # Tennessee Valley Authority (TVA)
    ZoneKey("US-CAR-CPLW"): ["SOUTH|CPLW"],  # CPL Retail Energy West (CPLW)
    ZoneKey("US-CAR-DUK"): ["SOUTH|DUKE"],  # Duke Energy
    ZoneKey("US-CAR-CPLE"): ["SOUTH|CPLE"],  # CPL Retail Energy East (CPLE)
    ZoneKey("US-NY-NYIS"): [
        "NEPTUNE|SAYR",  # NYISO (Neptune)
        "LINDENVFT|LINDEN",  # NYISO (Linden)
        "HUDSONTP|HTP",  # NYISO (Hudson)
        "NYIS|NYIS",  # "NYISO LMP"
    ],
}

FUEL_MAPPING = {
    "Coal": "coal",
    "Gas": "gas",
    "Hydro": "hydro",
    "Multiple Fuels": "unknown",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other": "unknown",
    "Other Renewables": "unknown",
    "Solar": "solar",
    "Storage": "battery",
    "Wind": "wind",
}


def _get_api_subscription_key(session: Session) -> str:
    response = session.get("https://dataminer2.pjm.com/config/settings.json")
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Could not get API key: {response.status_code}: {response.text}",
        )
    return response.json()["subscriptionKey"]


def _fetch_api_data(
    kind: Literal[
        "load_frcstd_7_day",
        "gen_by_fuel",
        "hourly_solar_power_forecast",
        "hourly_wind_power_forecast",
        "da_hrl_lmps",
        "rt_unverified_fivemin_lmps",
    ],
    params: dict,
    session: Session,
) -> dict:
    headers = {
        "Ocp-Apim-Subscription-Key": _get_api_subscription_key(session=session),
        "Accept-Encoding": "identity",
    }
    url = f"{US_PROXY}/{DATA_PATH}/{kind}"
    resp: Response = session.get(
        url=url, params={"host": "https://api.pjm.com", **params}, headers=headers
    )
    if (resp.status_code == 200) and (kind != "load_frcstd_7_day"):
        data = resp.json()
        return data
    elif (resp.status_code == 200) and (kind == "load_frcstd_7_day"):
        decompressed_data = gzip.decompress(resp.content)
        data = json.loads(decompressed_data)
        return data
    else:
        raise ParserException(
            PARSER,
            f"{kind} data is not available in the API: {resp.status_code}: {resp.text}",
        )


def fetch_consumption_forecast(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Gets consumption forecast 7 days ahead for PJM zone. Hourly data in MW."""

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    session = session or Session()
    # startRow must be set if forecast_area is set. RTO_COMBINED is area for whole PJM zone.
    params = {"download": True, "startRow": 1, "forecast_area": "RTO_COMBINED"}
    data = _fetch_api_data(kind="load_frcstd_7_day", params=params, session=session)

    consumption_list = TotalConsumptionList(logger)
    for elem in data:
        utc_datetime = elem["forecast_datetime_beginning_utc"]
        consumption_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(utc_datetime).replace(tzinfo=timezone.utc),
            source=SOURCE,
            consumption=elem["forecast_load_mw"],
            sourceType=EventSourceType.forecasted,
        )
    return consumption_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Uses PJM API to get generation by fuel.

    We assume that storage is battery storage (see https://learn.pjm.com/energy-innovations/energy-storage)
    """
    target_datetime = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    session = session or Session()

    params = {
        "startRow": 1,
        "rowCount": 500,
        "fields": "datetime_beginning_utc,fuel_type,mw",
        "datetime_beginning_utc": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }
    resp_data = _fetch_api_data(kind="gen_by_fuel", params=params, session=session)

    items = resp_data.get("items", [])

    if items == []:
        raise ParserException(
            parser=PARSER,
            message=f"{target_datetime}: Production data is not available in the API",
            zone_key=zone_key,
        )

    production_breakdown_list = ProductionBreakdownList(logger)
    for key, group in groupby(items, itemgetter("datetime_beginning_utc")):
        dt = datetime.fromisoformat(key).replace(tzinfo=timezone.utc)
        production = ProductionMix()
        storage = StorageMix()
        for data in group:
            mode = FUEL_MAPPING[data["fuel_type"]]
            value = data["mw"]
            if mode == "battery":
                storage.add_value(mode, -value)
            else:
                production.add_value(mode, value)
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            production=production,
            storage=storage,
            source=SOURCE,
        )

    return production_breakdown_list.to_list()


def fetch_wind_solar_forecasts(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Uses PJM API to request the wind and solar forecast (in MW) for a given date in hourly intervals."""

    session = session or Session()

    # Datetime
    target_datetime = (
        datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if target_datetime is None
        else target_datetime.astimezone(timezone.utc)
    )

    # Config for url
    params = {
        "startRow": 1,
        "rowCount": 10000,
        "datetime_beginning_utc": target_datetime.strftime("%Y-%m-%dT%H:00:00.0000000"),
    }

    resp_data_wind = _fetch_api_data(
        kind="hourly_wind_power_forecast", params=params, session=session
    )
    items_wind = resp_data_wind.get("items", [])

    resp_data_solar = _fetch_api_data(
        kind="hourly_solar_power_forecast", params=params, session=session
    )
    items_solar = resp_data_solar.get("items", [])

    # Combine wind and solar data and sort by datetime_beginning_utc
    items = items_wind + items_solar
    items.sort(key=itemgetter("datetime_beginning_utc", "evaluated_at_utc"))
    production_list = ProductionBreakdownList(logger)

    # Group by datetime_beginning_utc and get the last evaluated_at_utc entry for each group
    for datetime_utc, group in groupby(items, key=itemgetter("datetime_beginning_utc")):
        group_list = list(group)
        wind_entries = [entry for entry in group_list if "wind_forecast_mwh" in entry]
        latest_entry_wind = max(wind_entries, key=itemgetter("evaluated_at_utc"))
        solar_entries = [entry for entry in group_list if "solar_forecast_mwh" in entry]
        latest_entry_solar = max(solar_entries, key=itemgetter("evaluated_at_utc"))

        production_mix = ProductionMix()
        production_mix.add_value(
            "solar",
            latest_entry_solar["solar_forecast_mwh"],
            correct_negative_with_zero=True,
        )
        production_mix.add_value(
            "wind",
            latest_entry_wind["wind_forecast_mwh"],
            correct_negative_with_zero=True,
        )

        production_list.append(
            zoneKey=zone_key,
            datetime=datetime.fromisoformat(datetime_utc).replace(tzinfo=timezone.utc),
            production=production_mix,
            source=SOURCE,
            sourceType=EventSourceType.forecasted,
        )

    return production_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_dayahead_locational_marginal_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetches hourly day-ahead LMPs for the target EPT day from PJM Data Miner 2."""
    session = session or Session()

    target_datetime = (
        datetime.now(timezone.utc) if target_datetime is None else target_datetime
    )
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    target_day = target_datetime.astimezone(TIMEZONE).strftime("%Y-%m-%d")

    params = {
        "startRow": 1,
        # 23 ZONE pnodes x 25 hours (DST fall-back day) = 575; headroom for
        # any ZONE pnodes PJM adds in the future, since type=ZONE is an open
        # server-side filter rather than an explicit pnode list.
        "rowCount": 1000,
        "type": "ZONE",
        "fields": "datetime_beginning_utc,pnode_id,pnode_name,type,total_lmp_da",
        "datetime_beginning_ept": f"{target_day}T00:00to{target_day}T23:59",
    }
    data = _fetch_api_data(kind="da_hrl_lmps", params=params, session=session)
    items = data.get("items", [])
    total_rows = data.get("totalRows", 0)
    if total_rows > len(items):
        raise ParserException(
            PARSER,
            f"da_hrl_lmps response incomplete: got {len(items)} of {total_rows} rows",
            zone_key,
        )
    if not items:
        logger.warning(f"No day-ahead LMP data for {target_day}")
        return []

    prices = LocationalMarginalPriceList(logger)
    for item in items:
        dt = datetime.fromisoformat(item["datetime_beginning_utc"]).replace(
            tzinfo=timezone.utc
        )
        prices.append(
            zoneKey=zone_key,
            datetime=dt,
            end_datetime=dt + timedelta(hours=1),
            price=item["total_lmp_da"],
            currency="USD",
            node=item["pnode_name"],
            source=SOURCE,
        )
    return prices.to_list()


@refetch_frequency(timedelta(minutes=30))
def fetch_realtime_locational_marginal_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """Fetches 5-minute real-time LMPs for the 35 minutes up to target_datetime
    from PJM Data Miner 2.

    Uses the unverified feed because it is the only one posted in near real
    time (~5 minute latency); the verified LMP feeds are only posted the next
    business day. Unverified values may later be revised in the verified
    feeds. The feed retains 15 days of data.
    """
    session = session or Session()

    target_datetime = (
        datetime.now(timezone.utc) if target_datetime is None else target_datetime
    )
    if target_datetime.tzinfo is None:
        target_datetime = target_datetime.replace(tzinfo=timezone.utc)
    # Filter on the UTC column: an EPT wall-clock window would be ambiguous
    # or nonexistent around the DST transitions.
    window_end = target_datetime.astimezone(timezone.utc)
    window_start = window_end - timedelta(minutes=35)
    utc_format = "%Y-%m-%dT%H:%M"
    # ZONE-type aggregate pnodes: PJM-RTO, MID-ATL/APS, and transmission zones.
    # The feed also carries bus-level pnodes, so this keeps the response focused
    # on aggregate locations.
    zone_pnode_ids = (
        "1;3;51291;51292;51293;51295;51296;51297;51298;51299;51300;51301;"
        "7633629;8394954;8445784;33092371;34508503;34964545;37737283;"
        "116013753;124076095;970242670;1709725933"
    )

    params = {
        "startRow": 1,
        # 23 ZONE pnodes x 8 intervals = 184; headroom on top of that.
        "rowCount": 500,
        "pnode_id": zone_pnode_ids,
        "fields": "datetime_beginning_utc,pnode_id,pnode_name,total_lmp_rt",
        "datetime_beginning_utc": f"{window_start.strftime(utc_format)}to{window_end.strftime(utc_format)}",
    }
    data = _fetch_api_data(
        kind="rt_unverified_fivemin_lmps", params=params, session=session
    )
    items = data.get("items", [])
    total_rows = data.get("totalRows", 0)
    if total_rows > len(items):
        raise ParserException(
            PARSER,
            f"rt_unverified_fivemin_lmps response incomplete: got {len(items)} of {total_rows} rows",
            zone_key,
        )
    if not items:
        logger.warning(f"No real-time LMP data between {window_start} and {window_end}")
        return []

    prices = LocationalMarginalPriceList(logger)
    for item in items:
        dt = datetime.fromisoformat(item["datetime_beginning_utc"]).replace(
            tzinfo=timezone.utc
        )
        prices.append(
            zoneKey=zone_key,
            datetime=dt,
            end_datetime=dt + timedelta(minutes=5),
            price=item["total_lmp_rt"],
            currency="USD",
            node=item["pnode_name"],
            source=SOURCE,
        )
    return prices.to_list()


def _get_interface_data(
    interface: str, session: Session
) -> list[tuple[datetime, float]]:
    """Fetches 5min data for any PJM interface in the current day."""

    # For some reason the US-MIDW-MISO data is on a chart at a different url
    if interface == "MISO":
        url = "https://www.pjm.com/Charts/MISO.aspx"
    else:
        url = f"http://www.pjm.com/Charts/InterfaceChartDM2.aspx?open={interface}"

    response = session.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    scripts = soup.find(
        "script",
        {
            "type": "text/javascript",
            "src": "/assets/js/Highcharts/HighCharts/highcharts.js",
        },
    )
    exchange_script = scripts.find_next_sibling("script")

    # x-axis (time)
    time_pattern = r"var timeArray = (\[(.*)\])"
    time_array = re.search(time_pattern, str(exchange_script)).group(1)
    time_vals = demjson.decode(time_array)

    # y-axis [right] (actual & scheduled load)
    load_pattern = r"var load = (\[(.*)\])"
    load = re.search(load_pattern, str(exchange_script)).group(1)
    load_actual = demjson.decode(load)[0]

    converted_flows = []
    today = datetime.combine(datetime.now(TIMEZONE), time(), tzinfo=TIMEZONE)
    for t, flow in zip(time_vals, load_actual, strict=True):
        # some tail values might be null
        if flow is None:
            continue

        # make sure to use %I and not %H for %p to take effect
        time_of_the_day = datetime.strptime(t, "%I:%M %p").replace(tzinfo=TIMEZONE)
        dt = today.replace(hour=time_of_the_day.hour, minute=time_of_the_day.minute)

        converted_flows.append((dt, float(flow)))

    return converted_flows


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two zones."""

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if target_datetime is not None:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse historical data",
            sorted_zone_keys,
        )

    if not session:
        session = Session()

    # PJM reports exports as negative.
    direction = -1 if sorted_zone_keys.startswith(ZONE_KEY) else 1

    neighbour = zone_key2 if zone_key1 == ZONE_KEY else zone_key1
    interfaces = ZONE_TO_PJM_INTERFACES[neighbour]

    # get flow data from each interface with neighbour and merge
    session = session or Session()
    ungrouped_exchange_lists = []
    for interface in interfaces:
        exchange_list = ExchangeList(logger)

        interface_data = _get_interface_data(interface, session=session)
        for dt, net_flow in interface_data:
            exchange_list.append(
                zoneKey=sorted_zone_keys,
                datetime=dt,
                source=SOURCE,
                netFlow=direction * net_flow,
            )

        ungrouped_exchange_lists.append(exchange_list)

    return ExchangeList.merge_exchanges(ungrouped_exchange_lists, logger).to_list()


def fetch_grid_alerts(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    GRID_ALERTS_PATH = "ep/pages/dashboard.jsf"
    GRID_ALERTS_SOURCE = "https://emergencyprocedures.pjm.com"

    if target_datetime is not None:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse historical data",
            zone_key,
        )

    session = session or Session()

    url = f"{US_PROXY}/{GRID_ALERTS_PATH}"
    headers = {
        "Accept-Encoding": "identity",
    }
    response: Response = session.get(
        url=url,
        params={
            "host": GRID_ALERTS_SOURCE,
        },
        headers=headers,
    )

    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching grid alerts error code: {response.status_code}: {response.text}",
            zone_key,
        )

    soup = BeautifulSoup(response.text, "html.parser")
    tbody = soup.find("tbody", {"id": "frmTable:tblPostings_data"})
    if not tbody:
        raise ParserException(
            PARSER,
            f"BeautifulSoup could not find the tbody element in the response from {GRID_ALERTS_SOURCE}/{GRID_ALERTS_PATH}, error code: {response.status_code}: {response.text}",
            zone_key,
        )

    alerts = GridAlertList(logger)
    for i, alert in enumerate(tbody.children):
        alertType = extract_alert_type(alert, i)
        message = extract_message(alert, i)
        startTime, endTime = extract_start_and_end_time(alert, i)
        locationRegion = alert.find(class_=re.compile(r"region-name")).text.strip()

        alerts.append(
            zoneKey=ZONE_KEY,
            locationRegion=locationRegion,
            source=SOURCE,
            alertType=alertType,
            message=message,
            issuedTime=startTime,
            startTime=startTime,
            endTime=endTime,
        )
    return alerts.to_list()


def extract_alert_type(alert: BeautifulSoup, i: int) -> GridAlertType:
    alertType = alert.find(
        "span",
        {"id": re.compile(f"frmTable:tblPostings:{i}:j_idt\\d+:txtPriority")},
    ).text.strip()
    if alertType == "Action":
        return GridAlertType.action
    else:
        return GridAlertType.informational


def extract_message(alert: BeautifulSoup, i: int) -> str:
    messageBody = alert.find(
        "span", {"id": f"frmTable:tblPostings:{i}:txtMessage"}
    ).text.strip()
    topic = alert.find(
        "span",
        {"id": re.compile(f"frmTable:tblPostings:{i}:j_idt\\d+:txtMessageTypeName")},
    ).text.strip()
    return f"{topic}\n{messageBody}"


def extract_start_and_end_time(
    alert: BeautifulSoup, i: int
) -> tuple[datetime, datetime]:
    startTime = alert.find(
        "span", {"id": f"frmTable:tblPostings:{i}:txtEffectiveStartTime"}
    ).text.strip()
    endTime = alert.find(
        "span", {"id": f"frmTable:tblPostings:{i}:txtEffectiveEndTime"}
    ).text.strip()
    startTime = datetime.strptime(startTime, "%m.%d.%Y %H:%M").replace(tzinfo=TIMEZONE)
    if endTime != "":
        endTime = datetime.strptime(endTime, "%m.%d.%Y %H:%M").replace(tzinfo=TIMEZONE)
    else:
        endTime = None
    return startTime, endTime


if __name__ == "__main__":
    print("fetch_consumption_forecast() ->")
    print(fetch_consumption_forecast())

    # print("fetch_production() ->")
    # print(fetch_production())

    """
    for neighbor in [
        "US-CAR-DUK",
        "US-CAR-CPLE",
        "US-CAR-CPLW",
        "US-MIDW-LGEE",
        "US-MIDW-MISO",
        "US-NY-NYIS",
        "US-TEN-TVA",
    ]:
        print(f"fetch_exchange(US-MIDA-PJM, {neighbor}) ->")
        print(fetch_exchange(ZONE_KEY, ZoneKey(neighbor)))
    """
    # print("fetch_wind_solar_forecasts() ->")
    # print(fetch_wind_solar_forecasts())
