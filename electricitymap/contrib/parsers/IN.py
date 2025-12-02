#!usr/bin/env python3

"""Parser for all of India"""

from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Response, Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

# TODO 1 Migrate the IN_WE and IN_EA consumption fetching to this parser, using the grid india data.
# TODO 2 Migrate the fetch_consumption in this file so that it uses the grid india data instead of meritindia.in.

# This parsers does not work locally with all VPN. It does not work with SurfShark, but it works with NordVPN. Local proxies could also be used.
IN_TZ = ZoneInfo("Asia/Kolkata")
START_DATE_RENEWABLE_DATA = datetime(2020, 12, 17, tzinfo=IN_TZ)
# 1 MU = 1 GWH = 1000 MWH then assume uniform production per hour -> 1000/24 = 41.6666 = 1/0.024
# So MU / 0.024 = MW
CONVERSION_DAILY_GWH_TO_HOURLY_MW = 0.024

# Some of the websites we use work with the VPC connector, some work without it.
INDIA_PROXY_NO_VPC_CONNECTOR = (
    "https://in-proxy-no-vpc-connector-jfnx5klx2a-el.a.run.app"
)

NPP_MODE_MAPPING = {
    "THER (GT)": "gas",
    "THERMAL": "coal",
    "HYDRO": "hydro",
    "THER (DG)": "oil",
    "NUCLEAR": "nuclear",
}
NPP_REGION_MAPPING = {
    "NORTHERN": "IN-NO",
    "EASTERN": "IN-EA",
    "WESTERN": "IN-WE",
    "SOUTHERN": "IN-SO",
    "NORTH EASTERN": "IN-NE",
}

GRID_INDIA_REGION_MAPPING = {
    "NR": "IN-NO",
    "ER": "IN-EA",
    "WR": "IN-WE",
    "SR": "IN-SO",
    "NER": "IN-NE",
    "TOTAL": "IN",
}

GRID_INDIA_REGION_MAPPING = {
    "IN-NO": "NR",
    "IN-EA": "ER",
    "IN-WE": "WR",
    "IN-SO": "SR",
    "IN-NE": "NER",
    "IN": "TOTAL",
}

GRID_INDIA_SOURCE = "grid-india.in"

CEA_REGION_MAPPING = {
    "northern region": "IN-NO",
    "western region": "IN-WE",
    "southern region": "IN-SO",
    "eastern region": "IN-EA",
    "north-eastern region": "IN-NE",
}

DEMAND_URL_MERITINDIA = (
    "{proxy}/StateWiseDetails/BindCurrentStateStatus?host=https://meritindia.in"
)

# States codes as on meritindia.in
STATE_CODES = {
    "andhra-pradesh": "AP",
    "arunachal-pradesh": "ACP",
    "assam": "ASM",
    "bihar": "BHR",
    "chandiagarh": "CHG",
    "chhattisgarh": "CTG",
    "dadra-nagar-haveli": "DNH",
    "daman-diu": "DND",
    "delhi": "DL",
    "goa": "GOA",
    "gujarat": "GJT",
    "haryana": "HRN",
    "himachal-pradesh": "HP",
    "jammu-kashmir": "JAK",
    "jharkhand": "JHK",
    "karnataka": "KRT",
    "kerala": "KRL",
    "madhya-pradesh": "MPD",
    "maharashtra": "MHA",
    "manipur": "MIP",
    "meghalaya": "MGA",
    "mizoram": "MZM",
    "nagaland": "NGD",
    "odisha": "ODI",
    "puducherry": "PU",
    "punjab": "PNB",
    "rajasthan": "RJ",
    "sikkim": "SKM",
    "tamil-nadu": "TND",
    "telangana": "TLG",
    "tripura": "TPA",
    "uttar-pradesh": "UP",
    "uttarakhand": "UTK",
    "west-bengal": "WB",
}


STATES_MAPPING = {
    "IN-NO": [
        "delhi",
        "haryana",
        "himachal-pradesh",
        "jammu-kashmir",
        "punjab",
        "rajasthan",
        "uttar-pradesh",
        "uttarakhand",
    ],
    "IN-WE": ["gujarat", "madya-pradesh", "maharashtra", "goa", "chhattisgarh"],
    "IN-EA": ["bihar", "west-bengal", "odisha", "sikkim"],
    "IN-NE": [
        "arunachal-pradesh",
        "assam",
        "meghalaya",
        "tripura",
        "mizoram",
        "nagaland",
        "manipur",
    ],
    "IN-SO": [
        "karnataka",
        "kerala",
        "tamil-nadu",
        "andhra-pradesh",
        "telangana",
        "puducherry",
    ],
}


def fetch_consumption_from_meritindia(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> TotalConsumptionList:
    """Fetches the live consumption from the Merit Order Despatch of Electricity.
    This source seems to be a bit more stable right now than vidyutpravah.in"""
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    import concurrent.futures

    total_consumption = 0
    futures = []

    def fetch_state_consumption(session, state):
        resp: Response = session.post(
            DEMAND_URL_MERITINDIA.format(proxy=INDIA_PROXY_NO_VPC_CONNECTOR),
            data={"StateCode": STATE_CODES[state]},
        )
        data = resp.json()[0]
        return float(str(data["Demand"]).replace(",", ""))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for state in STATES_MAPPING[zone_key]:
            future = executor.submit(fetch_state_consumption, session, state)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            total_consumption += future.result()

    consumption_list = TotalConsumptionList(logger=logger)
    consumption_list.append(
        zoneKey=ZoneKey(zone_key),
        datetime=datetime.now(tz=IN_TZ),
        consumption=total_consumption,
        source="meritindia.in",
    )
    return consumption_list


def fetch_npp_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> dict[str, Any]:
    """Gets production for conventional thermal, nuclear and hydro from NPP daily reports
    This data most likely doesn't inlcude distributed generation"""

    npp_url = f"https://npp.gov.in/public-reports/cea/daily/dgr/{target_datetime:%d-%m-%Y}/dgr2-{target_datetime:%Y-%m-%d}.xls"
    r: Response = session.get(npp_url)

    if r.status_code == 200:
        df_npp = pd.read_excel(r.content, header=3)
        # Since 15/04/2025, a footer was added to the excel file.
        # It modifies the structure of its columns. By removing the footer and then removing the empty columns, we can have a consistent structure.
        df_npp = df_npp[df_npp[df_npp.columns[0]].notnull()]
        df_npp = df_npp.dropna(axis="columns", how="all")
        df_npp = df_npp.rename(
            columns={
                df_npp.columns[0]: "power_station",
                df_npp.columns[2]: "production_mode",
                "TODAY'S\nACTUAL\n": "value",
            }
        )
        df_npp["region"] = (
            df_npp["power_station"].apply(lambda x: NPP_REGION_MAPPING.get(x)).ffill()
        )
        df_npp = df_npp[["region", "production_mode", "value"]]

        df_npp_filtered = df_npp.loc[~df_npp["production_mode"].isna()].copy()

        df_zone = df_npp_filtered.loc[df_npp_filtered["region"] == zone_key].copy()
        df_zone["production_mode"] = df_zone["production_mode"].map(NPP_MODE_MAPPING)
        production_in_zone = df_zone.groupby(["production_mode"])["value"].sum()
        production_dict = {
            mode: round(production_in_zone.get(mode), 3)
            for mode in production_in_zone.index
        }
        return production_dict
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} conventional production data is not available : [{r.status_code}]",
        )


def fetch_consumption(
    zone_key: ZoneKey,
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    return fetch_consumption_from_meritindia(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        logger=logger,
    ).to_list()


def format_ren_production_data(
    content: bytes, zone_key: str, target_datetime: datetime
) -> dict[str, Any]:
    """Formats daily renewable production data for each zone"""
    df_ren = pd.read_excel(content, engine="openpyxl", header=5)
    df_ren = df_ren.dropna(axis=0, how="all")

    # They changed format of the data from 2024/07/01
    if target_datetime < datetime(2024, 7, 1, 0, 0, tzinfo=IN_TZ):
        df_ren = df_ren.rename(
            columns={
                df_ren.columns[1]: "region",
                df_ren.columns[2]: "wind",
                df_ren.columns[3]: "solar",
                df_ren.columns[4]: "unknown",
            }
        )
    else:
        # columns 4-7 are cumulative values for the month
        df_ren = df_ren.rename(
            columns={
                df_ren.columns[0]: "region",
                df_ren.columns[1]: "wind",
                df_ren.columns[2]: "solar",
                df_ren.columns[3]: "unknown",
            }
        )

    is_region = df_ren["region"].str.contains("Region")
    # values should be "{Indian name}/{English name}"
    df_ren["zone_key"] = (
        df_ren["region"]
        .loc[is_region]
        .str.split("/")
        .str[1]
        .str.lower()
        .map(CEA_REGION_MAPPING)
    )

    zone_data = df_ren.loc[
        (df_ren["zone_key"] == zone_key), ["wind", "solar", "unknown"]
    ]
    if zone_data.shape != (1, 3):
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} renewable production data is not available",
        )
    zone_data = zone_data.iloc[0, :].to_dict()

    return zone_data


def fetch_cea_production(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> dict[str, Any] | None:
    """Gets production data for wind, solar and other renewables
    Other renewables includes a share of hydro, biomass and others and will categorized as unknown
    DISCLAIMER: this data is only available since 2020/12/17"""
    cea_data_url = (
        "https://cea.nic.in/wp-admin/admin-ajax.php?action=getpostsfordatatables"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0",
    }

    retry_strategy = Retry(
        total=3,  # Total number of retries
        backoff_factor=1,  # A delay factor to apply between attempts
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],  # A set of HTTP status codes that we should force a retry on
        allowed_methods=[
            "GET"
        ],  # Set of uppercased HTTP method verbs that we should retry on.
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    r_all_data: Response = session.get(cea_data_url, headers=headers, verify=False)
    if r_all_data.status_code == 200:
        all_data = r_all_data.json()["data"]
        target_elem = [
            elem
            for elem in all_data
            if target_datetime.strftime("%Y-%m-%d") in elem["date"]
        ]

        if len(target_elem) > 0 and target_elem[0]["link"] != "file_not_found":
            target_url = target_elem[0]["link"].split(": ")[0]
            formatted_url = target_url.split("^")[0]
            r: Response = session.get(formatted_url, headers=headers, verify=False)
            renewable_production = format_ren_production_data(
                content=r.content, zone_key=zone_key, target_datetime=target_datetime
            )
            return renewable_production
        else:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: {zone_key} renewable production data is not available",
            )
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} renewable production data is not available, {r_all_data.status_code}",
        )


def fetch_grid_india_report(
    target_datetime: datetime, session: Session
) -> tuple[datetime, bytes | None]:
    """
    Rely on grid-india.in backend API to fetch data report.
    First query the backend to get the list of files available for a given date.
    Reports can be found here : https://grid-india.in/en/reports/daily-psp-report
    And also here here : https://report.grid-india.in/index.php?p=

    """

    GRID_INDIA_BACKEND_URL = "https://webapi.grid-india.in"
    GRID_INDIA_CDN_URL = "https://webcdn.grid-india.in"

    GRID_INDIA_BACKEND_WITH_PROXY_URL = (
        f"{INDIA_PROXY_NO_VPC_CONNECTOR}/api/v1/file?host={GRID_INDIA_BACKEND_URL}"
    )

    # Reports are stored per fiscal year, which goes from April N to March N+1.
    fiscal_year_start = (
        target_datetime.year - 1 if target_datetime.month < 4 else target_datetime.year
    )
    fiscal_year_end_short = (fiscal_year_start + 1) % 100

    payload = {
        "_source": "GRDW",
        "_type": "DAILY_PSP_REPORT",
        "_fileDate": f"{fiscal_year_start}-{fiscal_year_end_short}",
        "_month": target_datetime.strftime("%m"),
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0",
        "Content-Type": "application/json",
    }

    r: Response = session.post(
        GRID_INDIA_BACKEND_WITH_PROXY_URL, json=payload, headers=headers
    )
    # We process the file that pass the file type filters and that is the most recent one
    # before target_datetime.
    if r.status_code == 200:
        file_list = r.json()["retData"]
        latest_file_url = None
        latest_file_date = None
        for file in file_list:
            is_correct_type = (
                file.get("MimeType") in ("attachment/xls", "application/vnd.ms-excel")
            ) and file.get("FileType") == "DAILY_PSP_REPORT"

            if is_correct_type:
                try:
                    # Title_ is expected to start with "dd.mm.yy"
                    file_date_str = file["Title_"].split("_")[0]
                    file_date = datetime.strptime(file_date_str, "%d.%m.%y").replace(
                        tzinfo=IN_TZ
                    )

                    if file_date <= target_datetime and (
                        latest_file_date is None or file_date > latest_file_date
                    ):
                        latest_file_date = file_date
                        latest_file_url = file.get("FilePath")
                except (ValueError, IndexError):
                    # Ignore files with titles that don't match the expected date format
                    continue

        if latest_file_url is not None:
            file_full_url = f"{INDIA_PROXY_NO_VPC_CONNECTOR}/{latest_file_url}?host={GRID_INDIA_CDN_URL}"
            r: Response = session.get(file_full_url, headers=headers)
            return latest_file_date, r.content
        else:
            raise ParserException(
                parser="IN.py",
                message=f"{target_datetime}: Grid India daily production data is not available",
            )
    else:
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: Grid India daily production data is not available, {r.status_code}",
        )


def get_daily_generation_table(content: bytes) -> pd.DataFrame:
    """
    Get the G. Sourcewise generation (Gross) (MU) table from the daily report.
    Returns a DataFrame with the generation for each mode.
    Shape of the dataframe :
    'mode' is the mode name.
    'value' is the generation, in MU/GWh :
    | mode | value |
    |------|-------|
    | coal | 100   |
    | lignite| 200   |
    | hydro | 300   |
    | nuclear | 400   |
    | gas | 500   |
    | unknown | 600   |
    """
    df = pd.read_excel(content, engine="xlrd", header=4)

    START_PATTERN = "Sourcewise generation"
    END_PATTERN = "Demand Diversity Factor"
    SECOND_END_PATTERN = "Total"

    description_column = df.columns[0]
    start_index = df.index[
        df[description_column].str.contains(START_PATTERN, na=False, case=False)
    ].tolist()[0]
    end_index = df.index[
        df[description_column].str.contains(END_PATTERN, na=False, case=False)
    ].tolist()[0]

    if not start_index or not end_index:
        raise ParserException(
            parser="IN.py",
            message="Could not find the generation table in the daily report; the format may have changed.",
        )
    generation_df = df.iloc[start_index + 1 : end_index, 0:]

    second_end_index = generation_df.index[
        generation_df[description_column].str.contains(
            SECOND_END_PATTERN, na=False, case=False
        )
    ].tolist()[0]

    if not second_end_index:
        raise ParserException(
            parser="IN.py",
            message="Could not find the second end of the generation table in the daily report; the format may have changed.",
        )
    total_row_position = generation_df.index.get_loc(
        generation_df[
            generation_df[description_column].str.contains("Total", na=False)
        ].index[0]
    )

    generation_df_without_re_share = generation_df.iloc[: total_row_position + 1, :]
    generation_df_without_re_share = generation_df_without_re_share.set_index(
        generation_df_without_re_share.columns[0]
    )
    generation_df_without_re_share.columns = generation_df_without_re_share.iloc[0]
    generation_df_without_re_share = generation_df_without_re_share.iloc[1:].dropna(
        axis=1, how="all"
    )
    generation_df_without_re_share.index.name = "mode"

    return generation_df_without_re_share


def get_wind_solar(content: bytes, zone_key: str) -> pd.DataFrame:
    """
    Gets the wind and solar production for a given zone key.
    Retrieves it from the daily report,
    in the A. Power Supply Position at All India and Regional level table.
    Returns a DataFrame with the wind and solar production for the given zone key.
    Shape of the dataframe :
    'mode' is 'wind' and 'solar'.
    'value' is the generation, in MU/GWh :
    | mode | value |
    |------|-------|
    | wind | 100   |
    | solar| 200   |
    """

    df = pd.read_excel(content, engine="xlrd", header=2)
    START_PATTERN = "A. Power Supply Position"
    END_PATTERN = "B. Frequency Profile"

    description_column = df.columns[0]

    start_mask = df[description_column].str.contains(
        START_PATTERN, na=False, case=False
    )
    end_mask = df[description_column].str.contains(END_PATTERN, na=False, case=False)
    start_index = start_mask[start_mask].first_valid_index()
    end_index = end_mask[end_mask].first_valid_index()

    if start_index is None or end_index is None:
        raise ParserException(
            parser="IN.py",
            message="Could not find the generation table in the daily report; the format may have changed.",
        )
    # Only keep the first table (A. Power Supply Position at All India and Regional level)
    generation_df = df.iloc[start_index + 1 : end_index].copy()

    # Set the row that contains the region names as the header.
    generation_df.columns = generation_df.iloc[0]
    generation_df = generation_df.iloc[1:].reset_index(drop=True)

    # The descriptions ('Wind Gen', etc.) are now in the first data column.
    # Let's search this column to find the integer index of the rows we want.
    description_col = generation_df.iloc[:, 0]
    wind_mask = description_col.str.contains("Wind Gen", na=False, case=False)
    solar_mask = description_col.str.contains("Solar Gen", na=False, case=False)
    wind_row_index = description_col[wind_mask].index[0]
    solar_row_index = description_col[solar_mask].index[0]

    region_column = GRID_INDIA_REGION_MAPPING[zone_key]
    wind_gen_nr = generation_df.loc[wind_row_index, region_column]
    solar_gen_nr = generation_df.loc[solar_row_index, region_column]

    wind_solar_df = pd.DataFrame(
        {"value": [wind_gen_nr, solar_gen_nr]}, index=["wind", "solar"]
    )
    wind_solar_df.index.name = "mode"
    wind_solar_df["value"] = pd.to_numeric(
        wind_solar_df["value"].replace("-", 0), errors="coerce"
    ).fillna(0)

    return wind_solar_df


def parse_daily_production_grid_india_report(
    content: bytes,
    zone_key: str,
    target_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Parses production data from grid india daily report.
    Will split the daily production evenly across the 24 hours of the day.
    This will then be reestimated by the estimation pipeline and the mode breakdown.
    """
    daily_production_breakdown = get_production_breakdown(
        content=content, zone_key=zone_key
    )
    daily_production_breakdown["value"] = (
        daily_production_breakdown["value"] / CONVERSION_DAILY_GWH_TO_HOURLY_MW
    )
    df_pivoted = daily_production_breakdown.T
    df_hourly = pd.concat([df_pivoted] * 24, ignore_index=True)

    # Next, create a DatetimeIndex for the 24 hours of the target_datetime
    start_of_day = target_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=IN_TZ
    )
    hourly_index = pd.date_range(start=start_of_day, periods=24, freq="H")

    # Set this as the index of your new DataFrame
    df_hourly.index = hourly_index

    all_data_points = ProductionBreakdownList(logger)
    for timestamp, production_series in df_hourly.iterrows():
        production_dict = production_series.dropna().to_dict()
        production_mix = ProductionMix()
        for mode, value in production_dict.items():
            production_mix.add_value(mode, value)
        all_data_points.append(
            zoneKey=ZoneKey(zone_key),
            datetime=timestamp.to_pydatetime(),
            production=production_mix,
            source=GRID_INDIA_SOURCE,
        )
    return all_data_points.to_list()


def parse_15m_production_grid_india_report(
    content: bytes,
    zone_key: str,
    target_datetime: datetime,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Parses production data from grid india report. Uses the 15-minute data in the TimeSeries sheet of the report.
    Since 15-minute data aggregated to daily values do not match the daily production value from the first sheet of the report, we rescale the 15-minute data so that the total matches the daily production value.
    Then, we assume that each zone has the same share of the production share for a given mode over the whole day.
    We then breakdown the (15-minute, country-level, per mode) data, to (15-minute, zone-level, per mode) data.
    """
    # Get total production for the whole country, from the daily data report.
    daily_india_generation = parse_daily_total_production_grid_india_report(
        content=content
    )
    # Get total production for the whole country, from the 15-minute time series report.
    _15min_india_generation_aggregated_daily = (
        parse_total_production_15min_grid_india_report(content=content)
    )

    # Compute the scaling factor that will be used to scale the 15-minute data so that its total matches the daily production value.
    generation_scaling_factor = (
        daily_india_generation / _15min_india_generation_aggregated_daily
    )
    # Scale the 15-minute data
    _15min_scaled_generation_df = scale_15min_production(
        content=content, scaling_factor=generation_scaling_factor
    )

    # Now, compute the share of the considered zone key in the India-level production, for each mode.
    zone_mode_share_out_of_country = compute_zone_key_share_per_mode_out_of_total(
        content=content, zone_key=zone_key
    )

    # Scale the 15-minute by the share of the mode for the considered zone key out of the country-level production.
    ## Do not scale the time column
    mode_columns = _15min_scaled_generation_df.columns.intersection(
        zone_mode_share_out_of_country.index
    )
    ordered_zone_mode_share_out_of_country = zone_mode_share_out_of_country.reindex(
        mode_columns
    )

    # Multiply the modes columns by the scaling factors
    _15min_scaled_generation_df[mode_columns] = _15min_scaled_generation_df[
        mode_columns
    ].mul(ordered_zone_mode_share_out_of_country)

    ## Convert the time column to a datetime index and drop the TIME column
    datetime_series = pd.to_datetime(
        target_datetime.strftime("%Y-%m-%d") + " " + _15min_scaled_generation_df["TIME"]
    )
    _15min_scaled_generation_df.index = datetime_series
    _15min_scaled_generation_df.index = _15min_scaled_generation_df.index.tz_localize(
        IN_TZ
    )
    _15min_scaled_generation_df = _15min_scaled_generation_df.drop(columns=["TIME"])

    all_data_points = ProductionBreakdownList(logger)
    for timestamp, production_series in _15min_scaled_generation_df.iterrows():
        production_dict = production_series.dropna().to_dict()
        production_mix = ProductionMix()
        for mode, value in production_dict.items():
            production_mix.add_value(mode, value)
        all_data_points.append(
            zoneKey=ZoneKey(zone_key),
            datetime=timestamp.to_pydatetime(),
            production=production_mix,
            source=GRID_INDIA_SOURCE,
        )
    return all_data_points.to_list()


def get_production_breakdown(content: bytes, zone_key: str) -> dict[str, Any]:
    """
    Computes the share of the zone key in the total production for each mode.
    Returns a dictionary with the mode as key and the share as value.
    We will then assume this percentage is uniform across the day.
    """
    daily_generation_df = get_daily_generation_table(content)
    if zone_key == "IN":
        zone_generation = daily_generation_df["All India"]
    else:
        zone_generation = daily_generation_df[GRID_INDIA_REGION_MAPPING[zone_key]]

    # Removes Total row
    modes = ["coal", "lignite", "hydro", "nuclear", "gas", "RES"]
    pattern = "|".join(modes)
    mask = zone_generation.index.str.contains(pattern, case=False, na=False)
    selected_df = zone_generation[mask]

    # Sum the 'Coal' and 'Lignite'
    numeric_df = selected_df.apply(pd.to_numeric, errors="coerce")
    coal_lignite_sum = numeric_df.loc[["Coal", "Lignite"]].sum()
    numeric_df.loc["coal"] = coal_lignite_sum
    all_modes_except_wind_solar = numeric_df.drop(["Coal", "Lignite"])
    all_modes_except_wind_solar_df = all_modes_except_wind_solar.to_frame(name="value")

    # Get wind and solar for the considered zone key
    wind_solar_india_df = get_wind_solar(content=content, zone_key=zone_key)

    all_modes_df = pd.concat([all_modes_except_wind_solar_df, wind_solar_india_df])
    all_modes_df.index = all_modes_df.index.str.lower()
    # Rename the "Gas, Naphta & Diesel" mode to "gas"
    gas_mask = all_modes_df.index.str.contains("gas", na=False)
    if gas_mask.any():
        old_gas_label = all_modes_df.index[gas_mask][0]
        all_modes_df = all_modes_df.rename(index={old_gas_label: "gas"})

    # RES contains wind, solar, biomass and others.
    # Substract wind and solar from RES, and map it to unknown.
    res_mask = all_modes_df.index.str.contains("res", na=False)
    if res_mask.any():
        old_res_label = all_modes_df.index[res_mask][0]
        all_modes_cleaned_df = all_modes_df.rename(index={old_res_label: "unknown"})

    # Replace any '-' strings with 0 and ensure the value column is numeric.
    # Coerce errors will turn any other non-numeric values into NaN, which we then fill with 0.
    all_modes_cleaned_df["value"] = pd.to_numeric(
        all_modes_cleaned_df["value"].replace("-", 0), errors="coerce"
    ).fillna(0)

    all_modes_cleaned_df.loc["unknown", "value"] = (
        all_modes_cleaned_df.loc["unknown", "value"]
        - all_modes_cleaned_df.loc["wind", "value"]
        - all_modes_cleaned_df.loc["solar", "value"]
    )

    return all_modes_cleaned_df


def compute_zone_key_share_per_mode_out_of_total(
    content: bytes, zone_key: str
) -> pd.Series:
    country_production_breakdown = get_production_breakdown(
        content=content, zone_key="IN"
    )
    zone_production_breakdown = get_production_breakdown(
        content=content, zone_key=zone_key
    )

    total_production_zone_share_out_of_country = (
        zone_production_breakdown.sum() / country_production_breakdown.sum()
    )["value"]

    zone_key_share_per_mode_out_of_country = (
        zone_production_breakdown["value"] / country_production_breakdown["value"]
    )

    # We ensure that all share are between 0 and 1.
    # If not, we replace the value by the share of the total production of the zone out of the total production of the country.
    condition = (zone_key_share_per_mode_out_of_country >= 0) & (
        zone_key_share_per_mode_out_of_country <= 1
    )

    return zone_key_share_per_mode_out_of_country.where(
        condition, total_production_zone_share_out_of_country
    )


def scale_15min_production(content: bytes, scaling_factor: float) -> pd.DataFrame:
    df = pd.read_excel(content, engine="xlrd", header=2, sheet_name="TimeSeries")

    KEYWORD_MAPPING = {
        "NUCLEAR": "nuclear",
        "WIND": "wind",
        "SOLAR": "solar",
        "HYDRO": "hydro",
        "GAS": "gas",
        "THERMAL": "coal",
        "OTHERS": "unknown",
    }

    # Columns names are like NUCLEAR\n(MW) or WIND**\n(MW), etc.
    # Try to make mapping robust by not relying on exact match.
    dynamic_rename_mapping = {}
    for col_name in df.columns:
        for source_mode, mode in KEYWORD_MAPPING.items():
            if source_mode.lower() in str(col_name).lower():
                dynamic_rename_mapping[col_name] = mode
                break

    df = df[list(dynamic_rename_mapping.keys()) + ["TIME"]]
    df.rename(columns=dynamic_rename_mapping, inplace=True)

    # The first and last rows are not part of the time series and should be deleted.
    df = df.iloc[1:-1].reset_index(drop=True)
    mode_columns = list(dynamic_rename_mapping.values())

    # Ensure all mode columns are numeric before scaling
    for col in mode_columns:
        df[col] = pd.to_numeric(df[col].replace("-", 0), errors="coerce").fillna(0)

    scaled_generation = df[mode_columns].mul(scaling_factor, axis=0)
    scaled_generation = pd.concat([df["TIME"], scaled_generation], axis=1)
    return scaled_generation


def parse_daily_total_production_grid_india_report(
    content: bytes,
) -> float:
    """
    Extract the total production across the whole country from the daily report.
    Returns it in MWh.
    """
    generation_df = get_daily_generation_table(content)
    # Data is in MU=GWh.
    total_generation = generation_df.loc["Total", "All India"]
    total_generation_numeric = pd.to_numeric(
        str(total_generation).replace("-", "0"), errors="coerce"
    )
    total_all_india_generation = total_generation_numeric * 1000
    return float(total_all_india_generation)


def parse_total_production_15min_grid_india_report(
    content: bytes,
) -> float:
    """
    Computes the total production from the 15-minute data, in MWh.
    """
    df = pd.read_excel(content, engine="xlrd", header=2, sheet_name="TimeSeries")
    total_gen_col = "TOTAL GENERATION\n(MW)"
    df[total_gen_col] = pd.to_numeric(df[total_gen_col], errors="coerce")
    df["15min_energy"] = df[total_gen_col] / 4
    total_generation_from_15_min = df["15min_energy"].sum()
    return float(total_generation_from_15_min)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Indian parser has a long history. There have been many sources being used, with different formats and different periods of availability.
    Here we try to resolve how to fetch and parse the production data for the given zone key and target datetime.
    """
    session = session or Session()
    if target_datetime is None:
        _target_datetime = datetime.now(tz=IN_TZ)
    else:
        if target_datetime.tzinfo is None:
            _target_datetime = target_datetime.replace(tzinfo=IN_TZ)
        else:
            _target_datetime = target_datetime.astimezone(IN_TZ)

    if _target_datetime > datetime(2024, 11, 4, tzinfo=IN_TZ):
        # PSP Reports with TimeSeries sheets are only available since 2024/11/04
        report_date, report_content = fetch_grid_india_report(
            target_datetime=_target_datetime, session=session
        )
        production_data = parse_15m_production_grid_india_report(
            content=report_content,
            zone_key=zone_key,
            target_datetime=report_date,
        )
        return production_data
    elif _target_datetime >= datetime(
        2023, 4, 1, tzinfo=IN_TZ
    ) and _target_datetime < datetime(2024, 11, 4, tzinfo=IN_TZ):
        # PSP Reports are available as spreadsheet since 2023/04/01, but without TimeSeries (15-minute) data.
        report_date, report_content = fetch_grid_india_report(
            target_datetime=_target_datetime, session=session
        )
        production_data = parse_daily_production_grid_india_report(
            content=report_content,
            zone_key=zone_key,
            target_datetime=report_date,
        )
        return production_data
    elif _target_datetime > START_DATE_RENEWABLE_DATA and _target_datetime < datetime(
        2023, 4, 1, tzinfo=IN_TZ
    ):
        production_data = parse_production_from_cea_npp(
            zone_key=zone_key,
            target_datetime=_target_datetime,
            session=session,
        )
        return production_data
    else:
        # An alternative here would be to parse the PDF from Grid India.
        raise ParserException(
            parser="IN.py",
            message=f"{target_datetime}: {zone_key} production data is not available before {START_DATE_RENEWABLE_DATA}",
        )


def parse_production_from_cea_npp(
    zone_key: str,
    target_datetime: datetime,
    session: Session = Session(),
    logger: Logger = getLogger(__name__),
) -> list[dict[str, Any]]:
    """
    Parses production data from CEA NPP.
    """
    renewable_production = {}
    try:
        renewable_production = fetch_cea_production(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
        )
    except ParserException:
        logger.warning(
            f"{zone_key}: renewable production not available for {target_datetime} - will compute production with conventional production only"
        )

    conventional_production = None
    try:
        conventional_production = fetch_npp_production(
            zone_key=zone_key,
            session=session,
            target_datetime=target_datetime,
        )
    except ParserException:
        logger.warning(
            f"{zone_key}: conventional production not available for {target_datetime} - do not return any production data"
        )

    if conventional_production is not None:
        production = {**conventional_production, **renewable_production}
        hourly_production_data = daily_to_hourly_production_data(
            target_datetime=target_datetime,
            production=production,
            zone_key=zone_key,
            logger=logger,
        )
    return hourly_production_data.to_list()


def daily_to_hourly_production_data(
    target_datetime: datetime, production: dict, zone_key: str, logger: Logger
) -> ProductionBreakdownList:
    """convert daily power production average to hourly values"""
    all_hourly_production = ProductionBreakdownList(logger)
    production_mix = ProductionMix()
    for mode, value in production.items():
        production_mix.add_value(mode, value / CONVERSION_DAILY_GWH_TO_HOURLY_MW)

    start_of_day_local = target_datetime.astimezone(IN_TZ).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    for hour in range(0, 24):
        all_hourly_production.append(
            zoneKey=ZoneKey(zone_key),
            datetime=start_of_day_local + timedelta(hours=hour),
            production=production_mix,
            source=GRID_INDIA_SOURCE,
        )
    return all_hourly_production


if __name__ == "__main__":
    print(fetch_production(target_datetime=datetime(2024, 12, 24), zone_key="IN-WE"))
    print(fetch_consumption(zone_key=ZoneKey("IN-NO")))
