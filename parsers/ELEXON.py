#!/usr/bin/env python3

"""
Parser that uses the ELEXON API to return the following data types.

Production
Exchanges

Documentation:
https://www.elexon.co.uk/wp-content/uploads/2017/06/
bmrs_api_data_push_user_guide_v1.1.pdf
"""

import re
from datetime import date, datetime, time, timedelta
from io import StringIO
from logging import Logger, getLogger
from typing import Dict, List, Optional

import arrow
import pandas as pd
import pytz
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException
from parsers.lib.utils import get_token
from parsers.lib.validation import validate

ELEXON_ENDPOINT = "https://api.bmreports.com/BMRS/{}/v1"

ESO_NATIONAL_GRID_ENDPOINT = (
    "https://api.nationalgrideso.com/api/3/action/datastore_search_sql"
)

# A specific report to query most recent data (within 1 month time span + forecast ahead)
ESO_DEMAND_DATA_UPDATE_ID = "177f6fa4-ae49-4182-81ea-0c6b35f26ca6"

REPORT_META = {
    "B1620": {"expected_fields": 13, "skiprows": 5},
    "FUELINST": {"expected_fields": 22, "skiprows": 1},
    "INTERFUELHH": {"expected_fields": 11, "skiprows": 0},
}

# 'hydro' key is for hydro production
# 'hydro storage' key is for hydro storage
RESOURCE_TYPE_TO_FUEL = {
    "Biomass": "biomass",
    "Fossil Gas": "gas",
    "Fossil Hard coal": "coal",
    "Fossil Oil": "oil",
    "Hydro Pumped Storage": "hydro storage",
    "Hydro Run-of-river and poundage": "hydro",
    "Nuclear": "nuclear",
    "Solar": "solar",
    "Wind Onshore": "wind",
    "Wind Offshore": "wind",
    "Other": "unknown",
}
# Mapping is ordered to match the FUELINST output file as there's no header.
FUEL_INST_MAPPING = {
    "CCGT": "gas",
    "OIL": "oil",
    "COAL": "coal",
    "NUCLEAR": "nuclear",
    "WIND": "wind",
    "PS": "solar",
    "NPSHYD": "hydro",
    "OCGT": "gas",
    "OTHER": "unknown",
    "INTFR": "exchange",
    "INTIRL": "exchange",
    "INTNED": "exchange",
    "INTEW": "exchange",
    "BIOMASS": "biomass",
    "INTNEM": "exchange",
    "INTELEC": "exchange",
    "INTIFA2": "exchange",
    "INTNSL": "exchange",
}

ESO_FUEL_MAPPING = {
    "EMBEDDED_WIND_GENERATION": "wind",
    "EMBEDDED_SOLAR_GENERATION": "solar",
    "PUMP_STORAGE_PUMPING": "hydro storage",
}

EXCHANGES = {
    "FR->GB": [3, 8, 9],  # IFA, Eleclink, IFA2
    "GB->GB-NIR": [4],
    "GB->NL": [5],
    "GB->IE": [6],
    "BE->GB": [7],
    "GB->NO-NO2": [10],  # North Sea Link
}


def _create_eso_historical_demand_index(session: Session) -> Dict[int, str]:
    """Get the ids of all historical_demand_data reports"""
    index = {}
    response = session.get(
        "https://data.nationalgrideso.com/demand/historic-demand-data/datapackage.json"
    )
    data = response.json()
    pattern = re.compile(r"historic_demand_data_(?P<year>\d+)")
    for resource in data["resources"]:
        match = pattern.match(resource["name"])
        if match is not None:
            index[int(match["year"])] = resource["id"]
    return index


def query_additional_eso_data(
    target_datetime: datetime, session: Session
) -> List[dict]:
    begin = (target_datetime - timedelta(days=1)).strftime("%Y-%m-%d")
    end = (target_datetime + timedelta(days=1)).strftime("%Y-%m-%d")
    if target_datetime > (datetime.now(tz=pytz.UTC) - timedelta(days=30)):
        report_id = ESO_DEMAND_DATA_UPDATE_ID
    else:
        index = _create_eso_historical_demand_index(session)
        report_id = index[target_datetime.year]
    params = {
        "sql": f'''SELECT * FROM "{report_id}" WHERE "SETTLEMENT_DATE" BETWEEN '{begin}' AND '{end}' ORDER BY "SETTLEMENT_DATE"'''
    }
    response = session.get(ESO_NATIONAL_GRID_ENDPOINT, params=params)
    return response.json()["result"]["records"]


def query_ELEXON(report, session: Session, params):
    params["APIKey"] = get_token("ELEXON_TOKEN")
    return session.get(ELEXON_ENDPOINT.format(report), params=params)


def query_exchange(session: Session, target_datetime=None):
    if target_datetime is None:
        target_datetime = date.today()

    from_date = (target_datetime - timedelta(days=1)).strftime("%Y-%m-%d")
    to_date = target_datetime.strftime("%Y-%m-%d")

    params = {"FromDate": from_date, "ToDate": to_date, "ServiceType": "csv"}
    response = query_ELEXON("INTERFUELHH", session, params)
    return response.text


def query_production(
    session: Session, target_datetime: Optional[datetime] = None, report: str = "B1620"
):
    if target_datetime is None:
        target_datetime = datetime.now()

    # we can only fetch one date at a time.
    # if target_datetime is first 30 minutes of the day fetch the day before.
    # otherwise fetch the day of target_datetime.
    if target_datetime.time() <= time(0, 30):
        settlement_date = target_datetime.date() - timedelta(1)
    else:
        settlement_date = target_datetime.date()

    params = {
        "SettlementDate": settlement_date.strftime("%Y-%m-%d"),
        "Period": "*",
        "ServiceType": "csv",
    }
    if report == "FUELINST":
        params = {
            "FromDateTime": (target_datetime - timedelta(days=1))
            .date()
            .strftime("%Y-%m-%d %H:%M:%S"),
            "ToDateTime": (target_datetime + timedelta(days=1))
            .date()
            .strftime("%Y-%m-%d %H:%M:%S"),
            "Period": "*",
            "ServiceType": "csv",
        }
    response = query_ELEXON(report, session, params)
    return response.text


def parse_exchange(
    zone_key1: str,
    zone_key2: str,
    csv_text: str,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if not csv_text:
        return None

    report = REPORT_META["INTERFUELHH"]

    sorted_zone_keys = sorted([zone_key1, zone_key2])
    exchange = "->".join(sorted_zone_keys)
    data_points = list()
    lines = csv_text.split("\n")

    # check field count in report is as expected
    field_count = len(lines[1].split(","))
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in INTERFUELHH report, got {}".format(
                report["expected_fields"], field_count
            )
        )

    for line in lines[1:-1]:
        fields = line.split(",")

        # settlement date / period combinations are always local time
        date = datetime.strptime(fields[1], "%Y%m%d").date()
        settlement_period = int(fields[2])
        date_time = datetime_from_date_sp(date, settlement_period)

        data = {
            "sortedZoneKeys": exchange,
            "datetime": date_time,
            "source": "bmreports.com",
        }

        # positive value implies import to GB
        multiplier = -1 if "GB" in sorted_zone_keys[0] else 1
        net_flow = 0.0  # init
        for column_index in EXCHANGES[exchange]:
            # read out all columns providing values for this exchange
            if fields[column_index] == "":
                continue  # no value provided for this exchange
            net_flow += float(fields[column_index]) * multiplier
        data["netFlow"] = net_flow
        data_points.append(data)

    return data_points


def parse_production_FUELINST(
    csv_data: str,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    """A temporary parser for the FUELINST report.
    This report will be decomissioned sometime in 2023.
    We use it as a replacement for B1620 that doesn't work
    at the moment (19/12/2022).
    """
    if not csv_data:
        raise ParserException("ELEXON.py", "Production file is empty.")
    report = REPORT_META["FUELINST"]
    # create DataFrame from slice of CSV rows
    df = pd.read_csv(StringIO(csv_data), skiprows=1, skipfooter=1, header=None)
    # check field count in report is as expected
    field_count = len(df.columns)
    if field_count != report["expected_fields"]:
        raise ParserException(
            "ELEXON.py",
            "Expected {} fields in FUELINST report, got {}".format(
                report["expected_fields"], len(df.columns)
            ),
        )
    # The file doesn't have a column header, so we need to recreate it.
    mapping = {1: "Settlement Date", 2: "Settlement Period", 3: "Spot Time"}
    for index, fuel in enumerate(FUEL_INST_MAPPING.values()):
        mapping[index + 4] = fuel
    df = df.rename(columns=mapping)
    df["Settlement Date"] = df["Settlement Date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d")
    )
    df["Settlement Period"] = df["Settlement Period"].astype(int)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["Settlement Date"], x["Settlement Period"]),
        axis=1,
    )
    return df.set_index("datetime")


def parse_additional_eso_production(raw_data: List[dict]) -> pd.DataFrame:
    """Parse additional eso data for embedded wind/solar and hydro storage."""
    df = pd.DataFrame.from_records(raw_data)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["SETTLEMENT_DATE"], x["SETTLEMENT_PERIOD"]),
        axis=1,
    )
    df = df.rename(columns=ESO_FUEL_MAPPING)
    return df.set_index("datetime")


def process_production_events(
    fuel_inst_data: pd.DataFrame, eso_data: pd.DataFrame
) -> List[dict]:
    """Combine FUELINST report and ESO data together to get the full picture and to EM Format."""
    df = fuel_inst_data.join(eso_data, rsuffix="_eso")
    df = df.rename(columns={"wind_eso": "wind", "solar_eso": "solar"})
    df = df.groupby(df.columns, axis=1).sum()
    data_points = list()
    for time in pd.unique(df.index):
        time_df = df[df.index == time]

        data_point = {
            "zoneKey": "GB",
            "datetime": time.to_pydatetime(),
            "source": "bmreports.com",
            "production": dict(),
            "storage": dict(),
        }

        for row in time_df.iterrows():
            electricity_production = row[1].to_dict()
            for key in electricity_production.keys():
                if key in PRODUCTION_MODES:
                    data_point["production"][key] = electricity_production[key]
                elif key == "hydro storage":
                    # According to National Grid Eso:
                    # The demand due to pumping at hydro pump storage units; the -ve signifies pumping load.
                    # We store the pump loading as a positive value and discharge as negative.
                    data_point["storage"]["hydro"] = -electricity_production[key]

        data_points.append(data_point)
    return data_points


def parse_production(
    csv_text: str,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    if not csv_text:
        return None

    report = REPORT_META["B1620"]

    # create DataFrame from slice of CSV rows
    df = pd.read_csv(StringIO(csv_text), skiprows=report["skiprows"] - 1)

    # check field count in report is as expected
    field_count = len(df.columns)
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in B1620 report, got {}".format(
                report["expected_fields"], len(df.columns)
            )
        )

    # filter out undesired columns
    df = df.iloc[:-1, [7, 8, 9, 4]]

    df["Settlement Date"] = df["Settlement Date"].apply(
        lambda x: datetime.strptime(x, "%Y-%m-%d")
    )
    df["Settlement Period"] = df["Settlement Period"].astype(int)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["Settlement Date"], x["Settlement Period"]),
        axis=1,
    )

    # map from report fuel names to electricitymap fuel names
    fuel_column = "Power System Resource  Type"
    df[fuel_column] = df[fuel_column].apply(lambda x: RESOURCE_TYPE_TO_FUEL[x])

    # loop through unique datetimes and create each data point
    data_points = list()
    for time in pd.unique(df["datetime"]):
        time_df = df[df["datetime"] == time]

        data_point = {
            "zoneKey": "GB",
            "datetime": time.to_pydatetime(),
            "source": "bmreports.com",
            "production": dict(),
            "storage": dict(),
        }

        for row in time_df.iterrows():
            fields = row[1].to_dict()
            fuel = fields[fuel_column]
            quantity = fields["Quantity"]

            # check if storage value and if so correct key
            if "storage" in fuel:
                fuel_key = fuel.replace("storage", "").strip()
                # ELEXON storage is negative when storing and positive when
                # discharging (the opposite to electricitymap)
                data_point["storage"][fuel_key] = quantity * -1
            else:
                # if/else structure allows summation of multiple quantities
                # e.g. 'Wind Onshore' and 'Wind Offshore' both have the
                # key 'wind' here.
                if fuel in data_point["production"].keys():
                    data_point["production"][fuel] += quantity
                else:
                    data_point["production"][fuel] = quantity

        data_points.append(data_point)

    return data_points


def datetime_from_date_sp(date, sp):
    datetime = arrow.get(date).shift(minutes=30 * (sp - 1))
    return datetime.replace(tzinfo="Europe/London").datetime


def _fetch_wind(
    target_datetime: Optional[datetime] = None, logger: Logger = getLogger(__name__)
):
    if target_datetime is None:
        target_datetime = datetime.now()

    # line up with B1620 (main production report) search range
    d = target_datetime.date()
    start = d - timedelta(hours=48)
    end = datetime.combine(d + timedelta(days=1), time(0))

    session = Session()
    params = {
        "FromDateTime": start.strftime("%Y-%m-%d %H:%M:%S"),
        "ToDateTime": end.strftime("%Y-%m-%d %H:%M:%S"),
        "ServiceType": "csv",
    }
    response = query_ELEXON("FUELINST", session, params)
    csv_text = response.text

    NO_DATA_TXT_ANSWER = "<httpCode>204</httpCode><errorType>No Content</errorType>"
    if NO_DATA_TXT_ANSWER in csv_text:
        logger.warning(f"Impossible to fetch wind data for {target_datetime}")
        return pd.DataFrame(columns=["datetime", "Wind"])

    report = REPORT_META["FUELINST"]
    df = pd.read_csv(
        StringIO(csv_text), skiprows=report["skiprows"], skipfooter=1, header=None
    )

    field_count = len(df.columns)
    if field_count != report["expected_fields"]:
        raise ValueError(
            "Expected {} fields in FUELINST report, got {}".format(
                report["expected_fields"], len(df.columns)
            )
        )

    df = df.iloc[:, [1, 2, 3, 8]]
    df.columns = ["Settlement Date", "Settlement Period", "published", "Wind"]
    df["Settlement Date"] = df["Settlement Date"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d")
    )
    df["Settlement Period"] = df["Settlement Period"].astype(int)
    df["datetime"] = df.apply(
        lambda x: datetime_from_date_sp(x["Settlement Date"], x["Settlement Period"]),
        axis=1,
    )

    df["published"] = df["published"].apply(
        lambda x: datetime.strptime(str(x), "%Y%m%d%H%M%S")
    )
    # get the most recently published value for each datetime
    idx = df.groupby("datetime")["published"].transform(max) == df["published"]
    df = df[idx]

    return df[["datetime", "Wind"]]


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
):
    session = session or Session()
    try:
        target_datetime = arrow.get(target_datetime).datetime
    except arrow.parser.ParserError:
        raise ValueError("Invalid target_datetime: {}".format(target_datetime))
    response = query_exchange(session, target_datetime)
    data = parse_exchange(zone_key1, zone_key2, response, target_datetime, logger)
    return data


# While using the FUELINST report we can increase the refetch frequency.
@refetch_frequency(timedelta(hours=6))
def fetch_production(
    zone_key: str = "GB",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    session = session or Session()
    try:
        target_datetime = arrow.get(target_datetime).datetime
    except arrow.parser.ParserError:
        raise ValueError("Invalid target_datetime: {}".format(target_datetime))
    # TODO currently resorting to FUELINST as B1620 reports 0 production in most production
    # modes at the moment. (16/12/2022) FUELINST will be decomissioned in 2023, so we should
    # switch back to B1620 at some point.
    response = query_production(session, target_datetime, "FUELINST")
    fuel_inst_data = parse_production_FUELINST(response, target_datetime, logger)
    raw_additional_data = query_additional_eso_data(target_datetime, session)
    additional_data = parse_additional_eso_production(raw_additional_data)
    data = process_production_events(fuel_inst_data, additional_data)
    # We are fetching from FUELINST directly.
    if False:
        # At times B1620 has had poor quality data for wind so fetch from FUELINST
        # But that source is unavailable prior to cutout date
        HISTORICAL_WIND_CUTOUT = "2016-03-01"
        FETCH_WIND_FROM_FUELINST = True
        if target_datetime < arrow.get(HISTORICAL_WIND_CUTOUT).datetime:
            FETCH_WIND_FROM_FUELINST = False
        if FETCH_WIND_FROM_FUELINST:
            wind = _fetch_wind(target_datetime, logger=logger)
            for entry in data:
                datetime = entry["datetime"]
                wind_row = wind[wind["datetime"] == datetime]
                if len(wind_row):
                    entry["production"]["wind"] = wind_row.iloc[0]["Wind"]
                else:
                    entry["production"]["wind"] = None

    required = ["coal", "gas", "nuclear", "wind"]
    expected_range = {
        # Historical data might be above the current capacity for coal
        "coal": (0, 20000),
        "gas": (100, 60000),
        "nuclear": (100, 56000),
        "wind": (0, 600000),
    }
    data = [
        x
        for x in data
        if validate(x, logger, required=required, expected_range=expected_range)
    ]

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_exchange(FR, GB) ->")
    print(fetch_exchange("FR", "GB"))

    print("fetch_exchange(GB, IE) ->")
    print(fetch_exchange("GB", "IE"))

    print("fetch_exchange(GB, NL) ->")
    print(fetch_exchange("GB", "NL"))
