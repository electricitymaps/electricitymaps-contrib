import logging
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import NamedTuple

import pandas as pd
from requests import Response, Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

REPORTS_ADMIN_URL = "https://www.iemop.ph/wp-admin/admin-ajax.php"
DIPC_URL = "https://www.iemop.ph/market-data/dipc-energy-results-raw/"
RTDHS_URL = "https://www.iemop.ph/market-data/rtd-hvdc-schedules/"

TIMEZONE = "Asia/Manila"
SOURCE = "iemop.ph"
REGION_TO_ZONE_KEY = {
    "LUZON": "PH-LU",
    "VISAYAS": "PH-VI",
    "MINDANAO": "PH-MI",
}
RESOURCE_NAME_TO_MODE = {
    "1ACNPC_G01": "biomass",
    "1AMBUK_U01": "hydro",
    "1AMBUK_U02": "hydro",
    "1AMBUK_U03": "hydro",
    "1ANDA_G01": "coal",
    "1APEC_G01": "coal",
    "1ARMSOL_G01": "solar",
    "1BAKUN_G01": "hydro",
    "1BINGA_U01": "hydro",
    "1BINGA_U02": "hydro",
    "1BINGA_U03": "hydro",
    "1BINGA_U04": "hydro",
    "1BOSUNG_G01": "solar",
    "1BT2020_G01": "biomass",
    "1BTNSOL_G01": "solar",
    "1BULSOL_G01": "solar",
    "1BURGOS_G01": "wind",
    "1BURGOS_G02": "solar",
    "1BURGOS_G03": "solar",
    "1CABSOL_G01": "solar",
    "1CAPRIS_G01": "wind",
    "1CASECN_G01": "hydro",
    "1CIP2_G01": "oil",
    "1CLASOL_G01": "solar",
    "1DALSOL_G01": "solar",
    "1GFII_G01": "biomass",
    "1GIFT_G01": "biomass",
    "1IBEC_G01": "biomass",
    "1IPOWER_G01": "biomass",
    "1IPOWER_G02": "unknown",
    "1MAEC_G01": "solar",
    "1MAGAT_U01": "hydro",
    "1MAGAT_U02": "hydro",
    "1MAGAT_U03": "hydro",
    "1MAGAT_U04": "hydro",
    "1MARSOL_G01": "solar",
    "1MARVEL_G01": "coal",
    "1MARVEL_G02": "coal",
    "1MASIWA_G01": "hydro",
    "1MSINLO_G01": "coal",
    "1MSINLO_G02": "coal",
    "1NIABAL_G01": "hydro",
    "1NMHC_G01": "hydro",
    "1NMHC_G03": "hydro",
    "1NWIND_G01": "wind",
    "1NWIND_G02": "wind",
    "1PETRON_G01": "unknown",
    "1PETSOL_G01": "solar",
    "1PNTBNG_U01": "hydro",
    "1PNTBNG_U02": "hydro",
    "1RASLAG_G01": "solar",
    "1RASLAG_G02": "solar",
    "1SABANG_G01": "hydro",
    "1SLANGN_G01": "hydro",
    "1SMBELL_G01": "hydro",
    "1SMC_G01": "coal",
    "1SMC_G02": "coal",
    "1SMC_G03": "coal",
    "1SPABUL_G01": "solar",
    "1SROQUE_U01": "hydro",
    "1SROQUE_U02": "hydro",
    "1SROQUE_U03": "hydro",
    "1SUAL_G01": "coal",
    "1SUAL_G02": "coal",
    "1SUBSOL_G01": "solar",
    "1S_ENRO_G01": "oil",
    "1T_ASIA_G01": "oil",
    "1UPPC_G01": "coal",
    "1YHGRN_G01": "solar",
    "1ZAMSOL_G01": "solar",
    "2MMPP_G01": "gas",
    "2PNGEA_G01": "gas",
    "2SMNRTH_G01": "solar",
    "2VALSOL_G01": "solar",
    "3ADISOL_G01": "solar",
    "3AVION_U01": "gas",
    "3AVION_U02": "gas",
    "3AWOC_G01": "wind",
    "3BART_G01": "hydro",
    "3BBEC_G01": "biomass",
    "3BOTOCA_G01": "hydro",
    "3CALACA_G01": "coal",
    "3CALACA_G02": "coal",
    "3CALIRY_G01": "hydro",
    "3CALSOL_G01": "solar",
    "3ILIJAN_G01": "gas",
    "3ILIJAN_G02": "gas",
    "3KAL_G01": "hydro_storage",
    "3KAL_G02": "hydro_storage",
    "3KAL_G03": "hydro_storage",
    "3KAL_G04": "hydro_storage",
    "3MALAYA_G01": "gas",
    "3MALAYA_G02": "gas",
    "3MEC_G01": "solar",
    "3MGPP_G01": "geothermal",
    "3ORMAT_G01": "geothermal",
    "3PAGBIL_G01": "coal",
    "3PAGBIL_G02": "coal",
    "3PAGBIL_G03": "coal",
    "3QPPL_G01": "coal",
    "3RCBMI_G01": "oil",
    "3RCBMI_G02": "oil",
    "3SLPGC_G01": "coal",
    "3SLPGC_G02": "coal",
    "3SLTEC_G01": "coal",
    "3SLTEC_G02": "coal",
    "3SNGAB_G01": "gas",
    "3STA-RI_G01": "gas",
    "3STA-RI_G02": "gas",
    "3STA-RI_G03": "gas",
    "3STA-RI_G04": "gas",
    "3STA-RI_G05": "gas",
    "3STA-RI_G06": "gas",
    "1ARAYSOL_G01": "solar",
    "1ARAYSOL_G02": "solar",
    "1BALWIND_G01": "wind",
    "1BTSOLEN_G01": "solar",
    "1CONSOL_G01": "solar",
    "1CURSOL_G02": "solar",
    "1GIGSOL_G01": "solar",
    "1PASQSOL_G01": "solar",
    "1PETSOL_G02": "solar",
    "2PNGYSOL_G01": "solar",
    "3SOLACE_G01": "solar",
    "1AMPHAW_G01": "hydro",
    "1BAKSIP_G01": "hydro",
    "1BINENG_G01": "hydro",
    "1BT2020_G02": "biomass",
    "1BUTAO_G01": "hydro",
    "1CAGBIO_G01": "biomass",
    "1CLEANG_G01": "biomass",
    "1GIFT_G02": "biomass",
    "1GNPD_U01": "coal",
    "1GNPD_U02": "coal",
    "1GRGOLD_G01": "biomass",
    "1HYPGRN_G01": "biomass",
    "1LASUER_U01": "biomass",
    "1LIMAY_U01": "gas",
    "1LIMAY_U02": "gas",
    "1LIMAY_U03": "gas",
    "1LIMAY_U04": "gas",
    "1LIMAY_U05": "gas",
    "1LIMAY_U06": "gas",
    "1LIMAY_U07": "gas",
    "1LIMAY_U08": "gas",
    "1MARIS_U01": "hydro",
    "1MARIS_U02": "hydro",
    "1MATUNO_G01": "hydro",
    "1MPGC_U01": "coal",
    "1MSINLO_G03": "coal",
    "1RASLAG_G03": "solar",
    "1SMC_G04": "coal",
    "1TERASU_G01": "solar",
    "1VSGRIP_G01": "biomass",
    "2ECOPRK_G01": "solar",
    "2ECOTAGA_G01": "solar",
    "2TMOBIL_G01": "oil",
    "2TMOBIL_G02": "oil",
    "2TMOBIL_G03": "oil",
    "2TMOBIL_G04": "oil",
    "3BACMAN_U01": "geothermal",
    "3BACMAN_U02": "geothermal",
    "3BACMAN_U03": "geothermal",
    "3BALUG_G01": "hydro",
    "3CADPI_G01": "biomass",
    "3CLBATO_G01": "hydro",
    "3INARI_G01": "hydro",
    "3LWERLAB_G01": "hydro",
    "3MAJAY_G01": "hydro",
    "3MGI_G02": "geothermal",
    "3PALAK_G01": "hydro",
    "3SBPL_G01": "coal",
    "3TIBAG_G01": "hydro",
    "3UPLAB_G01": "hydro",
    "4LGPP_G01": "geothermal",
    "4PHSOL_G01": "solar",
    "4SEPSOL_G01": "solar",
    "5CEDC_U01": "coal",
    "5CEDC_U02": "coal",
    "5CEDC_U03": "coal",
    "5KSPC_G01": "coal",
    "5KSPC_G02": "coal",
    "5TOLSOL_G01": "solar",
    "5TPC_G01": "oil",
    "5TPC_G02": "coal",
    "6AMLA_G01": "hydro",
    "6CARSOL_G01": "solar",
    "6CENPRI_U01": "oil",
    "6CENPRI_U02": "oil",
    "6CENPRI_U03": "oil",
    "6CENPRI_U04": "oil",
    "6FFHC_G01": "biomass",
    "6HELIOS_G01": "solar",
    "6HPCO_G01": "biomass",
    "6MANSOL_G01": "solar",
    "6MNTSOL_G01": "solar",
    "6NASULO_G01": "geothermal",
    "6PAL1A_G01": "geothermal",
    "6PAL2A_U01": "geothermal",
    "6PAL2A_U02": "geothermal",
    "6PAL2A_U03": "geothermal",
    "6PAL2A_U04": "geothermal",
    "6SACASL_G01": "solar",
    "6SACASL_G02": "solar",
    "6SACSUN_G01": "solar",
    "6SCBE_G01": "oil",
    "6SLYSOL_G01": "solar",
    "6URC_G01": "biomass",
    "6VMC_G01": "biomass",
    "7JANOPO_G01": "hydro",
    "7LOBOC_G01": "hydro",
    "8CASA_G01": "biomass",
    "8COSMO_G01": "solar",
    "8GLOBAL_G01": "unknown",
    "8PALM_G01": "coal",
    "8PEDC_U01": "coal",
    "8PEDC_U02": "coal",
    "8PEDC_U03": "coal",
    "8PWIND_G01": "wind",
    "8SLWIND_G01": "wind",
    "8SUWECO_G01": "hydro",
    "4CLBYBNK_G01": "oil",
    "4IASMOD_G01": "oil",
    "4IASMOD_G02": "oil",
    "4IASMOD_G03": "oil",
    "4IASMOD_G04": "oil",
    "4IASMOD_G05": "oil",
    "4IASMOD_G06": "oil",
    "4TAFT_G01": "hydro",
    "5CPPC_U01": "oil",
    "5CPPC_U02": "oil",
    "5CPPC_U03": "oil",
    "5CPPC_U04": "oil",
    "5CPPC_U05": "oil",
    "5CPPC_U06": "oil",
    "5CPPC_U07": "oil",
    "5CPPC_U08": "oil",
    "5CPPC_U09": "oil",
    "5EAUC_U01": "coal",
    "5EAUC_U02": "coal",
    "5EAUC_U03": "coal",
    "5EAUC_U04": "coal",
    "5THVI_U01": "coal",
    "5THVI_U02": "coal",
    "5TPVI_U01": "oil",
    "5TPVI_U02": "oil",
    "5TPVI_U03": "oil",
    "5TPVI_U04": "oil",
    "5TPVI_U05": "oil",
    "5TPVI_U06": "oil",
    "6BISCOM_G01": "biomass",
    "6CABI_G01": "biomass",
    "6CENPRI_U05": "oil",
    "6HPCO_G02": "biomass",
    "6NTNEGB_G01": "biomass",
    "6SCBIOP_G01": "biomass",
    "6STNEGB_G01": "biomass",
    "6VMC_G02": "biomass",
    "7BDPP_U01": "oil",
    "7BDPP_U02": "oil",
    "7BDPP_U03": "oil",
    "7BDPP_U04": "oil",
    "7LOBOC_G02": "hydro",
    "7SEVILL_G01": "hydro",
    "7TPLPB4_U01": "oil",
    "7TPLPB4_U02": "oil",
    "7TPLPB4_U03": "oil",
    "7TPLPB4_U04": "oil",
    "8PDPP1_U02": "oil",
    "8PDPP1_U03": "oil",
    "8PDPP1_U05": "oil",
    "8STBPB1_U01": "oil",
    "8STBPB1_U02": "oil",
    "8STBPB1_U03": "oil",
    "8STBPB1_U04": "oil",
    "8TIMBA_G01": "hydro",
    "11KBSOL_G01": "solar",
    "13DIGSOL_G01": "solar",
    "14ASTROSOL_G01": "solar",
    "14NVSOL_G01": "solar",
    "9KEGJIM_G01": "oil",
    "9PANABNK_U01": "unknown",
    "9PANABNK_U02": "unknown",
    "9WMPC_U01": "oil",
    "9WMPC_U02": "oil",
    "9WMPC_U03": "oil",
    "9WMPC_U04": "oil",
    "9WMPC_U05": "oil",
    "9WMPC_U06": "oil",
    "9WMPC_U07": "oil",
    "9WMPC_U08": "oil",
    "9WMPC_U09": "oil",
    "10AGUS1_U01": "hydro",
    "10AGUS1_U02": "hydro",
    "10AGUS2_U01": "hydro",
    "10AGUS2_U02": "hydro",
    "10AGUS2_U03": "hydro",
    "10AGUS4_U01": "hydro",
    "10AGUS4_U02": "hydro",
    "10AGUS4_U03": "hydro",
    "10AGUS5_U01": "hydro",
    "10AGUS5_U02": "hydro",
    "10AGUS6_U01": "hydro",
    "10AGUS6_U02": "hydro",
    "10AGUS6_U03": "hydro",
    "10AGUS6_U04": "hydro",
    "10AGUS6_U05": "hydro",
    "10AGUS7_U01": "hydro",
    "10AGUS7_U02": "hydro",
    "10GNPK_U01": "coal",
    "10GNPK_U02": "coal",
    "10GNPK_U03": "coal",
    "10GNPK_U04": "coal",
    "10IDPP_G01": "oil",
    "10MEGC_G01": "oil",
    "10PPEI_U01": "coal",
    "11FDC_U01": "coal",
    "11FDC_U02": "coal",
    "11FDC_U03": "coal",
    "11FGBPC_G01": "hydro",
    "11KEGMAR_G01": "biomass",
    "11KIRAS_G01": "solar",
    "11MANFOR_G01": "hydro",
    "11MANFOR_G02": "hydro",
    "11MINBAL_G01": "oil",
    "11MINBU_G01": "hydro",
    "11MNCBLG_G01": "hydro",
    "11MNRGY_G01": "oil",
    "11MNRGY_G02": "oil",
    "11NBPC_G01": "oil",
    "11PACERM_G01": "oil",
    "11PKBUK_G01": "oil",
    "11PULA4_U01": "hydro",
    "11PULA4_U02": "hydro",
    "11PULA4_U03": "hydro",
    "11STEAG_U01": "coal",
    "11STEAG_U02": "coal",
    "12ASIGA_G01": "hydro",
    "12KEGGIN_G01": "oil",
    "12KEGTAN_G01": "oil",
    "12LKMAINIT_G01": "hydro",
    "12NACSUR_G01": "oil",
    "12PKSFRA_U01": "oil",
    "12PKSFRA_U02": "oil",
    "12TM2_U01": "oil",
    "12TM2_U02": "oil",
    "13DCPP_U01": "coal",
    "13DCPP_U02": "coal",
    "13EUROH_G01": "hydro",
    "13MAGDBNK_G01": "oil",
    "13MATIBNK_G01": "oil",
    "13MPCDIG_G01": "oil",
    "13SIBULAN_G01": "hydro",
    "13SMC_U01": "coal",
    "13SMC_U02": "coal",
    "13TALOM1_G01": "hydro",
    "13TALOM23_G01": "hydro",
    "13TM1_U01": "oil",
    "13TM1_U02": "oil",
    "13TUDAY2_G01": "hydro",
    "14ALMADA_G01": "hydro",
    "14BIOGS_G01": "biomass",
    "14BIOMS_U01": "biomass",
    "14GERBIO_G01": "biomass",
    "14LAMSAN_G01": "biomass",
    "14MARBEL_U01": "hydro",
    "14MTAPO_U01": "geothermal",
    "14MTAPO_U02": "geothermal",
    "14MTAPO_U03": "geothermal",
    "14PKPSOC_G01": "oil",
    "14SARANG_U01": "coal",
    "14SARANG_U02": "coal",
    "14SPGI_U01": "biomass",
    "14SUPKOR_G01": "oil",
    "1ANGAT_A": "hydro",
    "1ANGAT_M": "hydro",
    "1BAUANG_GS2": "oil",
    "1BAUANG_GS3": "oil",
    "1BAUANG_GS1": "oil",
    "1CNCEP_BAT": "battery",
    "1LAMAO_BAT": "battery",
    "1LIMAY_BAT": "battery",
    "1BTSOLEN_BAT": "battery",
    "1MAGAT_BAT": "battery",
    "1MSINLO_BAT": "battery",
    "1SNMAN_BAT": "battery",
    "1MAGAPIT_BAT": "battery",
    "3INGRID_GS1": "oil",
    "3INGRID_GS4": "oil",
    "3INGRID_GS6": "oil",
    "3INGRID_GS2": "oil",
    "3INGRID_GS3": "oil",
    "3INGRID_GS5": "oil",
    "3MKBN_A": "geothermal",
    "3MKBN_E": "geothermal",
    "3ALMNOS_BAT1": "battery",
    "3ALMNOS_BAT2": "battery",
    "3MKBN_B": "geothermal",
    "3MKBN_C": "geothermal",
    "3MKBN_D": "geothermal",
    "3TIWI_A": "geothermal",
    "3TIWI_C": "geothermal",
    "4ORMOC_BAT": "battery",
    "5CPPC_U10": "oil",
    "5TOLEDO_BAT": "battery",
    "6KABAN_BAT": "battery",
    "7UBAY_BAT": "battery",
    "8PDPP3_C": "oil",
    "8PDPP3_E": "oil",
    "8PDPP3_G": "oil",
    "8PDPP3_H": "oil",
    "9WMPC_U10": "oil",
    "11JASA_BAT": "battery",
    "11VILLA_BAT": "battery",
    "13MALITA_BAT": "battery",
    "13MACO_BAT": "battery",
}
EXCHANGE_KEY_MAPPING = {
    "MINVIS1": {"zone_key": "PH-MI->PH-VI", "flow": 1},
    "VISLUZ1": {"zone_key": "PH-LU->PH-VI", "flow": -1},
}
KIND_TO_URL = {"production": DIPC_URL, "exchange": RTDHS_URL}
KIND_TO_POST_ID = {"production": "5754", "exchange": "5770"}
STORAGE_METHODS_TO_MODE = {"hydro_storage": "hydro", "battery": "battery"}
MODES_TO_RESOURCE_KIND = {
    **{m: "production" for m in PRODUCTION_MODES},
    **{m: "storage" for m in STORAGE_METHODS_TO_MODE},
}


def _validate_resource_name_to_mode_mapping():
    for resource_name, mode in RESOURCE_NAME_TO_MODE.items():
        if mode not in set(PRODUCTION_MODES).union(STORAGE_METHODS_TO_MODE.keys()):
            raise ValueError(
                f"Resource {resource_name} has an unknown mode {mode} in RESOURCE_NAME_TO_MODE"
            )


class MarketReportsItem(NamedTuple):
    datetime: datetime
    filename: str
    link: str


def get_all_market_reports_items(
    session: Session, zone_key: ZoneKey, kind: str, logger: Logger = getLogger(__name__)
) -> dict[datetime, MarketReportsItem]:
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
        "post_id": KIND_TO_POST_ID[kind],
    }
    res = session.post(REPORTS_ADMIN_URL, data=form_data, verify=False)
    id_to_items = res.json().get("data", {})
    if not id_to_items:
        raise ParserException(
            parser="IEMOP.py",
            zone_key=zone_key,
            message=f"No reports available to fetch {kind} data",
        )
    datetime_to_items = {}
    for report_id, items in id_to_items.items():
        market_reports_item = MarketReportsItem(
            datetime.strptime(items["date"], "%d %B %Y %H:%M"),
            items["filename"],
            KIND_TO_URL[kind] + f"?md_file={report_id}",
        )
        datetime_to_items[market_reports_item.datetime] = market_reports_item
    logger.info(
        f"{zone_key} - {kind}: Succesfully recovered {len(datetime_to_items)} market reports items"
    )
    return datetime_to_items


def filter_reports_items(
    kind: str,
    zone_key: ZoneKey,
    reports_items: dict[datetime, MarketReportsItem],
    target_datetime: datetime | None,
) -> list[MarketReportsItem]:
    # Date filtering
    if target_datetime is None:
        last_available_datetime = max(reports_items.keys())
        start_datetime = last_available_datetime - timedelta(days=1)
        _exception_date = start_datetime.date()
        _reports_items = [
            item for item in reports_items.values() if item.datetime >= start_datetime
        ]
    else:
        # Refetch the whole day
        _exception_date = target_datetime.date()
        _reports_items = [
            item
            for item in reports_items.values()
            if item.datetime.date() == target_datetime.date()
        ]

    if len(_reports_items) == 0:
        raise ParserException(
            parser="IEMOP.py",
            zone_key=zone_key,
            message=f"{zone_key}: No {kind} data available for {_exception_date} ",
        )

    return _reports_items


def download_production_market_reports_items(
    session: Session, reports_items: list[MarketReportsItem], logger: Logger
) -> pd.DataFrame:
    from io import BytesIO
    from zipfile import ZipFile

    COLUMNS_MAPPING = {
        "REGION_NAME": "zone_key",
        "RESOURCE_NAME": "resource_name",
        "SCHED_MW": "value",
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
                        _df = convert_column_to_datetime(_df, "TIME_INTERVAL")
                        # Localize to TIMEZONE
                        _df["datetime"] = _df["datetime"].dt.tz_localize(TIMEZONE)
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

    # Add kind column for production/storage
    df.loc[:, "resource_kind"] = ""

    logger.info(
        f"Succesfully extracted unit level production between the {df.datetime.min()} and the {df.datetime.max()}"
    )

    return df


def filter_for_zone(df: pd.DataFrame, zone_key: ZoneKey) -> pd.DataFrame:
    df = df.copy()
    return df.query(f"zone_key == '{zone_key}'")


def filter_valid_values(df: pd.DataFrame, logger: Logger) -> pd.DataFrame:
    df = df.copy()
    # Filter out non generation resources - with the exception of storage resources
    df_production = df[df["resource_kind"] == "production"]
    df_production = df_production[df_production["value"] >= 0]
    df_storage = df[df["resource_kind"] == "storage"]
    df = pd.concat([df_production, df_storage])
    # Remove duplicates if there is discharge
    df = df.drop_duplicates(
        subset=["datetime", "zone_key", "resource_name"], keep="first"
    )
    # Fill a list of all unknown resources
    unknown_resources = df[df["mode"] == "unknown"]["resource_name"].unique()
    logger.warning(
        f"PH - production: Unknown resources found: {unknown_resources}. Please report this issue to the Electricity Maps team"
    )
    return df


def match_resources_to_modes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Remove 0 padding in resource name
    df["resource_name"] = df["resource_name"].apply(lambda x: x.strip("0"))
    # Match resource name to mode
    df["mode"] = df["resource_name"].apply(
        lambda x: RESOURCE_NAME_TO_MODE.get(x, "unknown")
    )
    # Match resource name to kind
    df["resource_kind"] = df["mode"].map(MODES_TO_RESOURCE_KIND)
    return df


def aggregate_per_datetime_mode(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["datetime", "mode", "resource_kind"])
        .sum(numeric_only=True)
        .reset_index()
    )


def pivot_per_mode(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Flatten columns and make them "{resource_kind}.{mode}"
    df["resource_kind_mode"] = df["resource_kind"] + "." + df["mode"]
    df = df[["resource_kind_mode", "datetime", "value"]].pivot(
        index="datetime", columns="resource_kind_mode"
    )
    df.columns = df.columns.droplevel()  # reset columns index

    # Handle storage
    df = df.rename(
        columns={
            f"storage.{storage_method}": f"storage.{storage_mode}"
            for storage_method, storage_mode in STORAGE_METHODS_TO_MODE.items()
        }
    )
    for storage_mode in STORAGE_METHODS_TO_MODE.values():
        col_name = f"storage.{storage_mode}"
        if col_name in df.columns:
            df[col_name] *= -1
    # With the pivot if some modes only have data for some datetimes, we will have NaNs
    # Fill them with 0
    df = df.fillna(0)
    return df


def download_exchange_market_reports_items(
    session: Session, reports_items: list[MarketReportsItem], logger: Logger
) -> pd.DataFrame:
    _all_items_df = []
    for reports_item in reports_items:
        logger.debug(f"Downloading market reports for {reports_item.filename}")
        r: Response = session.get(reports_item.link)
        _df = pd.read_csv(r.url)
        _df = _df[:-1]
        _df = convert_column_to_datetime(_df, "RUN_TIME")
        _df["zone_key"] = _df["HVDC_NAME"].apply(
            lambda x: EXCHANGE_KEY_MAPPING[x]["zone_key"]
        )
        _df["net_flow"] = _df.apply(
            lambda x: EXCHANGE_KEY_MAPPING[x["HVDC_NAME"]]["flow"] * x["FLOW_FROM"],
            axis=1,
        )
        _df = _df[["datetime", "zone_key", "net_flow"]]
        _all_items_df.append(_df)

    df = (
        pd.concat(_all_items_df, ignore_index=True)
        .set_index("datetime")
        .tz_localize(TIMEZONE)
    )
    return df


def convert_column_to_datetime(df: pd.DataFrame, datetime_column: str) -> pd.DataFrame:
    """convert datetime column to datetime format"""
    dt1 = pd.to_datetime(
        df[datetime_column],
        format="%m/%d/%Y %I:%M:%S %p",
        errors="coerce",
    )
    dt2 = pd.to_datetime(df[datetime_column], format="%m/%d/%Y", errors="coerce")
    df["datetime"] = dt1.combine_first(dt2)
    return df


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("PH-LU"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    session = session or Session()
    _validate_resource_name_to_mode_mapping()
    reports_items = get_all_market_reports_items(
        session, zone_key, "production", logger
    )
    reports_items = filter_reports_items(
        "production", zone_key, reports_items, target_datetime
    )

    df = download_production_market_reports_items(session, reports_items, logger)
    df = (
        df.pipe(filter_for_zone, zone_key)
        .pipe(match_resources_to_modes)
        .pipe(filter_valid_values, logger)
        .pipe(aggregate_per_datetime_mode)
        .pipe(pivot_per_mode)
    )

    production_breakdown = ProductionBreakdownList(logger)
    for tstamp, row in df.iterrows():
        production_mix = ProductionMix()
        for mode in [m for m in row.index if "production." in m]:
            production_mix.add_value(mode.replace("production.", ""), row[mode])
        storage_mix = StorageMix()
        for mode in [m for m in row.index if "storage." in m]:
            storage_mix.add_value(mode.replace("storage.", ""), row[mode])
        production_breakdown.append(
            zone_key,
            tstamp.to_pydatetime(),
            SOURCE,
            production_mix,
            storage_mix,
            sourceType=EventSourceType.measured,
        )

    return production_breakdown.to_list()


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    session = session or Session()
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    all_exchange_items = get_all_market_reports_items(
        session, sorted_zone_keys, "exchange", logger
    )
    reports_items = filter_reports_items(
        "exchange", sorted_zone_keys, all_exchange_items, target_datetime
    )

    df = download_exchange_market_reports_items(session, reports_items, logger).pipe(
        filter_for_zone, sorted_zone_keys
    )

    # Convert to EventList
    exchange_list = ExchangeList(logger)
    for tstamp, row in df.iterrows():
        exchange_list.append(
            zoneKey=row["zone_key"],
            datetime=tstamp.to_pydatetime(),
            netFlow=row["net_flow"],
            source=SOURCE,
        )
    return exchange_list.to_list()


if __name__ == "__main__":
    logger = getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    # print(fetch_production())
    # print(fetch_production(ZoneKey("PH-VI"), target_datetime=datetime(2023, 8, 15)))
    print(fetch_exchange(ZoneKey("PH-LU"), ZoneKey("PH-VI")))
    print(
        fetch_exchange(
            ZoneKey("PH-MI"), ZoneKey("PH-VI"), target_datetime=datetime(2023, 8, 15)
        )
    )
