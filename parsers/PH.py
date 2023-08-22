import logging
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Dict, List, NamedTuple, Optional, Union

import pandas as pd
import requests
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency

DIPC_URL = "https://www.iemop.ph/market-data/dipc-energy-results-raw/"
TIMEZONE = "Asia/Manila"
REGION_TO_ZONE_KEY = {
    "LUZON": "PH-LU",
    "VISAYAS": "PH-VI",
    "MINDANAO": "PH-MI",
}
RESOURCE_NAME_TO_MODE = {
    "1SUAL_G01": "coal",
    "3ILIJAN_G02": "gas",
    "3ILIJAN_G01": "gas",
    "3QPPL_G01": "coal",
    "1MARVEL_G02": "coal",
    "3PAGBIL_G01": "coal",
    "3CALACA_G02": "coal",
    "3CALACA_G01": "coal",
    "1MSINLO_G02": "coal",
    "1MSINLO_G01": "coal",
    "3STA-RI_G05": "gas",
    "3STA-RI_G06": "gas",
    "3STA-RI_G03": "gas",
    "3STA-RI_G04": "gas",
    "3STA-RI_G01": "gas",
    "3STA-RI_G02": "gas",
    "3SNGAB_G01": "gas",
    "3SLPGC_G02": "coal",
    "1CASECN_G01": "hydro",
    "3SLTEC_G02": "coal",
    "3SLTEC_G01": "coal",
    "3BACMAN_G01": "geothermal",
    "1SMC_G01": "coal",
    "3TIWI_C": "geothermal",
    "1MARVEL_G01": "coal",
    "3PAGBIL_G03": "coal",
    "1SMC_G02": "coal",
    "3MKBN_A": "geothermal",
    "1BAKUN_G01": "hydro",
    "1MAGAT_U03": "hydro",
    "1ANDA_G01": "coal",
    "1MAGAT_U04": "hydro",
    "1MAGAT_U02": "hydro",
    "3MKBN_B": "geothermal",
    "3KAL_G02": "hydro_storage",
    "1BURGOS_G01": "wind",
    "3KAL_G01": "hydro_storage",
    "1SROQUE_U02": "hydro",
    "1MAGAT_U01": "hydro",
    "3MALAYA_G02": "gas",
    "3MKBN_D": "geothermal",
    "1HEDCOR_G01": "hydro",
    "3TIWI_A": "geothermal",
    "3SLPGC_G01": "coal",
    "1SROQUE_U03": "hydro",
    "1AMBUK_U01": "hydro",
    "3MKBN_E": "geothermal",
    "1BINGA_U02": "hydro",
    "1BINGA_U01": "hydro",
    "1BINGA_U03": "hydro",
    "3BACMAN_G02": "geothermal",
    "1BINGA_U04": "hydro",
    "3MGPP_G01": "geothermal",
    "1CAPRIS_G01": "wind",
    "1AMBUK_U03": "hydro",
    "1IBEC_G01": "biomass",
    "1AMBUK_U02": "hydro",
    "1ANGAT_M": "hydro",
    "1SROQUE_U01": "hydro",
    "1APEC_G01": "coal",
    "3AVION_U01": "gas",
    "3CALIRY_G01": "hydro",
    "1ANGAT_A": "hydro",
    "3AWOC_G01": "wind",
    "3AVION_U02": "gas",
    "1GIFT_G01": "biomass",
    "1BT2020_G01": "biomass",
    "1IPOWER_G01": "biomass",
    "1PNTBNG_U01": "hydro",
    "1PETSOL_G01": "solar",
    "1SABANG_G01": "hydro",
    "1PNTBNG_U02": "hydro",
    "3CALSOL_G01": "solar",
    "1LIMAY_B": "gas",
    "1BAUANG_G01": "oil",
    "2TMO_G03": "oil",
    "3MEC_G01": "solar",
    "2TMO_G01": "oil",
    "1S_ENRO_G01": "oil",
    "1SUBSOL_G01": "solar",
    "1NWIND_G02": "wind",
    "1MASIWA_G01": "hydro",
    "2TMO_G02": "oil",
    "1NIABAL_G01": "hydro",
    "1NWIND_G01": "wind",
    "3BBEC_G01": "biomass",
    "1MAEC_G01": "solar",
    "2TMO_G04": "oil",
    "1CLASOL_G01": "solar",
    "1NMHC_G01": "hydro",
    "1MARSOL_G01": "solar",
    "1PETRON_G01": "unknown",
    "3BOTOCA_G01": "hydro",
    "1BULSOL_G01": "solar",
    "1RASLAG_G02": "solar",
    "1SLANGN_G01": "hydro",
    "1RASLAG_G01": "solar",
    "1LIMAY_A": "gas",
    "3ORMAT_G01": "geothermal",
    "1CABSOL_G01": "solar",
    "1YHGRN_G01": "solar",
    "1CIP2_G01": "oil",
    "2VALSOL_G01": "solar",
    "2MMPP_G01": "gas",
    "3KAL_G03": "hydro_storage",
    "1NMHC_G03": "hydro",
    "1SMBELL_G01": "hydro",
    "1ARMSOL_G01": "solar",
    "2PNGEA_G01": "gas",
    "1DALSOL_G01": "solar",
    "1ZAMSOL_G01": "solar",
    "1BURGOS_G02": "solar",
    "1SPABUL_G01": "solar",
    "1BURGOS_G03": "solar",
    "3ADISOL_G01": "solar",
    "1BTNSOL_G01": "solar",
    "3RCBMI_G01": "oil",
    "3RCBMI_G02": "oil",
    "3PAGBIL_G02": "coal",
    "3LIAN_G01": "biomass",
    "1BOSUNG_G01": "solar",
    "2SMNRTH_G01": "solar",
    "1ACNPC_G01": "biomass",
    "1GFII_G01": "biomass",
    "1IPOWER_G02": "unknown",
    "3MKBN_C": "geothermal",
    "3MALAYA_G01": "gas",
    "3BART_G01": "hydro",
    "3SLPGC_G03": "coal",
    "1MSNLO_BATG": "battery storage",
    "3HDEPOT_G01": "solar",
    "1SMC_G03": "coal",
    "3TIWI_B": "geothermal",
    "3SLPGC_G04": "coal",
    "1SUAL_G02": "coal",
    "1T_ASIA_G01": "oil",
    "1UPPC_G01": "coal",
    "3KAL_G04": "hydro_storage",
    "4LEYTE_A": "geothermal",
    "5TPC_G02": "coal",
    "8PEDC_U03": "coal",
    "6PAL1A_G01": "geothermal",
    "5KSPC_G02": "coal",
    "5KSPC_G01": "coal",
    "8PALM_G01": "coal",
    "5CEDC_U03": "coal",
    "5CEDC_U01": "coal",
    "5CEDC_U02": "coal",
    "8PEDC_U02": "coal",
    "8PEDC_U01": "coal",
    "6NASULO_G01": "geothermal",
    "4LGPP_G01": "geothermal",
    "6HELIOS_G01": "solar",
    "8PDPP3_G01": "oil",
    "5CPPC_G01": "oil",
    "6PAL2A_U01": "geothermal",
    "6PAL2A_U02": "geothermal",
    "8PWIND_G01": "wind",
    "5TOLSOL_G01": "solar",
    "6PAL2A_U03": "geothermal",
    "6MANSOL_G01": "solar",
    "4SEPSOL_G01": "solar",
    "6CARSOL_G01": "solar",
    "6SACASL_G02": "solar",
    "8SUWECO_G01": "hydro",
    "6SACASL_G01": "solar",
    "5CDPPI_G02": "oil",
    "5EAUC_G01": "oil",
    "4PHSOL_G01": "solar",
    "8PDPP_G01": "oil",
    "6SACSUN_G01": "solar",
    "6SLYSOL_G01": "solar",
    "8SLWIND_G01": "wind",
    "7BDPP_G01": "oil",
    "6MNTSOL_G01": "solar",
    "5TPC_G01": "oil",
    "5CDPPI_G01": "oil",
    "7JANOPO_G01": "hydro",
    "6FFHC_G01": "biomass",
    "8GLOBAL_G01": "unknown",
    "7LOBOC_G01": "hydro",
    "8COSMO_G01": "solar",
    "8STBAR_PB": "oil",
    "6AMLA_G01": "hydro",
    "8STBAR_PB2": "oil",
    "6SCBE_G01": "oil",
    "5PHNPB3_G01": "oil",
    "8PDPP3_G": "oil",
    "8CASA_G01": "biomass",
    "8AVON_G01": "oil",
    "6VMC_G01": "biomass",
    "6URC_G01": "biomass",
    "8PPC_G01": "oil",
    "6PAL2A_U04": "geothermal",
    "8PDPP3_H": "oil",
    "8PDPP3_D": "oil",
    "5LBGT_G01": "gas",
    "6HPCO_G01": "biomass",
    "8GUIM_G01": "wind",
    "6PAL2A_G01": "geothermal",
    "8PDPP3_F": "oil",
    "8PDPP3_C": "oil",
    "6CENPRI_U01": "oil",
    "6CENPRI_U02": "oil",
    "6CENPRI_U03": "oil",
    "6CENPRI_U04": "oil",
    "8PDPP3_E": "oil",
    "5LBGT_G02": "gas",
}


class MarketReportsItem(NamedTuple):
    datetime: datetime
    filename: str
    link: str


def get_all_market_reports_items(logger) -> Dict[datetime, MarketReportsItem]:
    """
    Gets a dictionary that converts a date into its code and filename
    """

    logger.debug("Fetching list of available market reports")
    form_data = {
        "action": "display_filtered_market_data_files",
        "datefilter%5Bstart%5D": "2021-09-13+00%3A00",
        "datefilter%5Bend%5D": "2021-09-13+12%3A20",
        "sort": "",
        "page": "1",
        "post_id": "5754",
    }
    r = requests.post(
        "https://www.iemop.ph/wp-admin/admin-ajax.php", data=form_data, verify=False
    )
    id_to_items = eval(r.text)["data"]
    datetime_to_items = {}
    for id, items in id_to_items.items():
        market_reports_item = MarketReportsItem(
            datetime.strptime(items["date"], "%d %B %Y %H:%M"),
            items["filename"],
            DIPC_URL + f"?md_file={id}",
        )
        datetime_to_items[market_reports_item.datetime] = market_reports_item
    logger.debug("Succesfully recovered market reports items")
    return datetime_to_items


def download_market_reports_items(
    session: Session, reports_items: List[MarketReportsItem], logger: Logger
) -> pd.DataFrame:
    from io import BytesIO
    from zipfile import ZipFile

    COLUMNS_MAPPING = {
        "REGION_NAME": "zone_key",
        "RESOURCE_NAME": "resource_name",
        "SCHED_MW": "production",
    }

    _all_items_df = []
    for reports_item in reports_items:
        logger.debug(f"Downloading market reports for {reports_item.filename}")
        res: Response = session.get(reports_item.link)
        _item_dfs = []
        # zip containing a list of csv files which we want to concatenate in a single dataframe
        with ZipFile(BytesIO(res.content)) as zip_file:
            for csv_filename in zip_file.namelist():
                if csv_filename.endswith(".csv"):
                    with zip_file.open(csv_filename) as csv_file:
                        _df = pd.read_csv(csv_file, header=0)
                        # The last line is EOF
                        _df = _df[:-1]
                        # All numeric types
                        _df = _df.apply(pd.to_numeric, errors="ignore")
                        # Add datetime column
                        # There can be two different formats
                        _dt1 = pd.to_datetime(
                            _df["TIME_INTERVAL"],
                            format="%m/%d/%Y %I:%M:%S %p",
                            errors="coerce",
                        )
                        _dt2 = pd.to_datetime(
                            _df["TIME_INTERVAL"], format="%m/%d/%Y", errors="coerce"
                        )
                        _df["datetime"] = _dt1.combine_first(_dt2)
                        # Localize to TIMEZONE
                        _df["datetime"] = _df["datetime"].apply(
                            lambda x: x.tz_localize(TIMEZONE)
                        )
                        # Remove 5 minute interval as we want start of interval convention
                        _df["datetime"] = _df["datetime"] - timedelta(minutes=5)
                        # Misc
                        _df["REGION_NAME"] = _df["REGION_NAME"].apply(
                            lambda x: REGION_TO_ZONE_KEY[x]
                        )
                        _df["filename"] = csv_filename
                        _df = _df[["datetime", "filename", *COLUMNS_MAPPING.keys()]]
                        _df = _df.rename(columns=COLUMNS_MAPPING)
                        _item_dfs.append(_df)

        _all_items_df.append(pd.concat(_item_dfs, ignore_index=True))

    df = pd.concat(_all_items_df, ignore_index=True)

    logger.info(
        f"Succesfully extracted unit level production between the {df.datetime.min()} and the {df.datetime.max()}"
    )

    return df


def filter_for_zone(df: pd.DataFrame, zone_key: ZoneKey) -> pd.DataFrame:
    df = df.copy()
    return df.query(f"zone_key == '{zone_key}'")


def filter_generation(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Filter out non generation resources
    df = df[df["production"] >= 0]
    return df


def match_resources_to_modes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Remove 0 padding in resource name
    df["resource_name"] = df["resource_name"].apply(lambda x: x.strip("0"))
    # Match resource name to mode
    df["mode"] = df["resource_name"].apply(
        lambda x: RESOURCE_NAME_TO_MODE[x] if x in RESOURCE_NAME_TO_MODE else "unknown"
    )
    return df


def aggregate_per_datetime_mode(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["datetime", "mode"]).sum(numeric_only=True).reset_index()


def pivot_per_mode(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.pivot(index="datetime", columns="mode")
    # Flatten columns and make them "production.{mode}"
    df.columns = df.columns.to_series().str.join(".")
    # Handle storage
    df = df.rename(columns={"production.hydro_storage": "storage.hydro"})
    df["storage.hydro"] *= -1
    return df


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = "PH-LU",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    reports_items = get_all_market_reports_items(logger)

    # Date filtering
    if target_datetime is None:
        last_available_datetime = max(reports_items.keys())
        start_datetime = last_available_datetime - timedelta(days=1)
        reports_item = [
            item for item in reports_items.values() if item.datetime >= start_datetime
        ]
    else:
        # Refetch the whole day
        reports_item = [
            item
            for item in reports_items.values()
            if item.datetime.date() == target_datetime.date()
        ]

    df = download_market_reports_items(session, reports_item, logger)
    df = (
        df.pipe(filter_for_zone, zone_key)
        .pipe(filter_generation)
        .pipe(match_resources_to_modes)
        .pipe(aggregate_per_datetime_mode)
        .pipe(pivot_per_mode)
    )

    production_breakdown = ProductionBreakdownList(logger)
    for datetime, row in df.iterrows():
        production_mix = ProductionMix()
        for mode in [m for m in row.index if "production." in m]:
            production_mix.add_value(mode.replace("production.", ""), row[mode])
        storage_mix = StorageMix()
        storage_mix.add_value("hydro", row["storage.hydro"])
        production_breakdown.append(
            zone_key,
            datetime,
            "iemop",
            production_mix,
            storage_mix,
            sourceType=EventSourceType.measured,
        )

    return production_breakdown.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> Union[List[dict], dict]:
    pass


if __name__ == "__main__":
    logger = getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    print(fetch_production())
