#!/usr/bin/env python3
import html
import re
import unicodedata
from datetime import date, datetime, timedelta
from io import BytesIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.types import ZoneKey

logger = getLogger(__name__)

# Live data: the backend of the charts on COES's "Portal de Información" page.
# Undocumented, half-hourly, up to the last half hour.
API_ENDPOINT = "https://www.coes.org.pe/Portal/portalinformacion/generacion"

# Refetches: COES's official daily operations report (IEOD), published one to two
# days later as one folder per day. Its TIPO_RECURSO sheet has the same half-hourly
# generation per fuel, with a finer split, and exists since ~2015-10.
IEOD_BROWSER = "https://www.coes.org.pe/Portal/browser/"
IEOD_ROOT = "Post Operación/Reportes/IEOD/"
# The annex with TIPO_RECURSO: Anexo_DDMM (2015-2017), Anexo1_Resumen_DDMM
# (2018-2025), AnexoA_DDMM (2026).
IEOD_ANNEX = re.compile(r"/Anexo(1_Resumen|A)?_\d{4}\.xlsx$", re.IGNORECASE)

TIMEZONE = ZoneInfo("America/Lima")

MAP_GENERATION = {
    "DIESEL": "oil",
    # Residual fuel oil, not biomass residues: COES's official daily report (IEOD)
    # splits this series into "RESIDUAL R500" and "RESIDUAL R6", two fuel oil
    # grades, and biomass has its own series (BAGAZO, BIOGÁS).
    "RESIDUAL": "oil",
    "CARBÓN": "coal",
    "GAS": "gas",
    "HÍDRICO": "hydro",
    "BIOGÁS": "biomass",
    "BAGAZO": "biomass",
    "SOLAR": "solar",
    "EÓLICA": "wind",
    "NAFTA & GAS REFINERÍA": "oil",
}

# IEOD TIPO_RECURSO columns, upper case without accents, as they have been named
# over the years.
IEOD_MAP_GENERATION = {
    "H. DE PASADA": "hydro",
    "H. PASADA": "hydro",
    "H.REGULACION": "hydro",
    "H. REGULACION": "hydro",
    "GAS NATURAL": "gas",
    "GN CAMISEA": "gas",
    "GAS DE CAMISEA": "gas",
    "GAS MALACAS": "gas",
    "GN MALACAS": "gas",
    "GAS DE MALACAS": "gas",
    "GAS AGUAYTIA": "gas",
    "GN AGUAYTIA": "gas",
    "GAS DE AGUAYTIA": "gas",
    "GAS LA ISLA": "gas",
    "GN LA ISLA": "gas",
    "CARBON": "coal",
    "DIESEL": "oil",
    "RESIDUAL": "oil",
    "RESIDUAL R500": "oil",
    "RESIDUAL R6": "oil",
    # Naphtha and gas from the Talara refinery's own power plant.
    "GAS REFINRI + NAFTA": "oil",
    "NAFTA+GAS DE REFINERIA": "oil",
    "NAFTA & GAS REFINERIA": "oil",
    "FLEXIGAS+GAS DE REFINERIA": "oil",
    "FLEXIGAS & GAS REFINERIA": "oil",
    "BAGAZO": "biomass",
    # The Maple Etanol sugarcane plant, which burns bagasse.
    "ETANOL": "biomass",
    "BIOGAS": "biomass",
    "SOLAR": "solar",
    "EOLICO": "wind",
    "EOLICA": "wind",
}
SOURCE = "coes.org.pe"


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("PE"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the production mix (in MW) of the target day and the day before."""
    session = session or Session()
    if target_datetime is None:
        today = datetime.now(tz=TIMEZONE).date()
        days = [
            _fetch_portal_day(session, d, logger)
            for d in (today - timedelta(days=1), today)
        ]
    else:
        if target_datetime.tzinfo is not None:
            target_datetime = target_datetime.astimezone(TIMEZONE)
        target_day = target_datetime.date()
        days = []
        for d in (target_day - timedelta(days=1), target_day):
            ieod_day = _fetch_ieod_day(session, d, logger)
            days.append(
                ieod_day
                if ieod_day is not None
                else _fetch_portal_day(session, d, logger)
            )
    df = pd.concat(days)

    production_breakdown_list = ProductionBreakdownList(logger)
    for dt, modes in zip(df.index.to_pydatetime(), df.to_dict("records"), strict=True):
        production = ProductionMix()
        for mode, value in modes.items():
            if pd.notna(value):
                production.add_value(mode, round(float(value), 3))
        production_breakdown_list.append(
            zoneKey=zone_key,
            datetime=dt,
            source=SOURCE,
            production=production,
        )
    return production_breakdown_list.to_list()


def _to_modes(
    df: pd.DataFrame, mapping: dict[str, str], logger: Logger
) -> pd.DataFrame:
    """Sums the fuel columns of `df` into production modes."""
    # COES returns every fuel it has ever had for every date (with zeros before a
    # fuel existed), so a new fuel name would otherwise break old dates too.
    unknown_sources = set(df.columns) - mapping.keys()
    for energy_source in sorted(unknown_sources):
        logger.warning(f"Unknown PE energy source {energy_source!r}, skipped")
    fuels_by_mode: dict[str, list[str]] = {}
    for fuel in df.columns:
        if fuel not in unknown_sources:
            fuels_by_mode.setdefault(mapping[fuel], []).append(fuel)
    return pd.DataFrame(
        {
            mode: df[fuels].sum(axis=1, min_count=1)
            for mode, fuels in fuels_by_mode.items()
        }
    )


def _fetch_portal_day(session: Session, day: date, logger: Logger) -> pd.DataFrame:
    """Production modes of `day` from the portal, half-hourly, labelled by their end."""
    response = session.post(
        API_ENDPOINT,
        data={
            "fechaInicial": day.strftime("%d/%m/%Y"),
            "fechaFinal": (day + timedelta(days=1)).strftime("%d/%m/%Y"),
            "indicador": 0,
        },
    )
    response.raise_for_status()
    # Data in MW (it is production not generation) + local time, be careful.
    series = response.json()["GraficoTipoCombustible"]["Series"]

    datetimes = [point["Nombre"] for point in series[0]["Data"]] if series else []
    for item in series:
        if [point["Nombre"] for point in item["Data"]] != datetimes:
            raise ValueError(
                f"Datetime values are not consistent across all sources for {day}"
            )
    df = pd.DataFrame(
        {item["Name"]: [point["Valor"] for point in item["Data"]] for item in series},
        index=pd.to_datetime(datetimes, format="%Y/%m/%d %H:%M:%S").tz_localize(
            TIMEZONE
        ),
        dtype=float,
    )

    # Since ~2026-03 this endpoint labels the solar series BAGAZO and the bagasse
    # series SOLAR, for every date (COES's official daily report, the IEOD, has the
    # same values under the right labels). Rather than hard-code the swap, which
    # would silently invert both if COES fixes it, tell them apart by shape: solar
    # is the one lower at night (also before Peru had solar, when it is 0 all day),
    # or if both are equal at night, the one that swings most during the day.
    if {"BAGAZO", "SOLAR"} <= set(df.columns):
        night, spread = df[df.index.hour < 5].mean(), df.max() - df.min()
        if (night["BAGAZO"], -spread["BAGAZO"]) < (night["SOLAR"], -spread["SOLAR"]):
            df = df.rename(columns={"BAGAZO": "SOLAR", "SOLAR": "BAGAZO"})

    return _to_modes(df, MAP_GENERATION, logger)


def _list_ieod_folder(session: Session, folder: str) -> list[str]:
    """Paths of the folders and files in an IEOD folder, as COES's file browser lists them."""
    response = session.post(
        IEOD_BROWSER + "vistadatos",
        data={
            "baseDirectory": IEOD_ROOT,
            "url": folder,
            "indicador": "S",
            "initialLink": "IEOD",
            "orderFolder": "D",
        },
    )
    response.raise_for_status()
    ids = (html.unescape(i) for i in re.findall(r'id="([^"]+)"', response.text))
    return [i for i in dict.fromkeys(ids) if i.startswith(folder) and i != folder]


def _fetch_ieod_day(session: Session, day: date, logger: Logger) -> pd.DataFrame | None:
    """Production modes of `day` from the IEOD, or None if it has no TIPO_RECURSO."""
    # Folder names vary over the years (07_JULIO/Día 01/, 07_Julio/01/), so they are
    # looked up rather than built.
    months = _list_ieod_folder(session, f"{IEOD_ROOT}{day.year}/")
    month = next((m for m in months if re.search(rf"/{day:%m}\D[^/]*/$", m)), None)
    if month is None:
        return None
    days = _list_ieod_folder(session, month)
    day_folder = next(
        (d for d in days if re.search(rf"/(D[IÍ]A )?{day:%d}/$", d, re.IGNORECASE)),
        None,
    )
    if day_folder is None:
        return None
    annex = next(
        (f for f in _list_ieod_folder(session, day_folder) if IEOD_ANNEX.search(f)),
        None,
    )
    if annex is None:
        return None

    response = session.get(IEOD_BROWSER + "download", params={"url": annex})
    response.raise_for_status()
    workbook = pd.ExcelFile(BytesIO(response.content))
    if "TIPO_RECURSO" not in workbook.sheet_names:
        return None
    sheet = pd.read_excel(
        workbook, sheet_name="TIPO_RECURSO", header=None, dtype=object
    )

    # A HORA header, then 48 half-hours until the TOTAL MWh row. The HORA cells are
    # times, strings, or a 1900-01-01 datetime for 24:00 depending on the year, so
    # the rows are dated by their position instead.
    header_row, hora_column = next(
        (r, c) for (r, c), value in sheet.stack().items() if value == "HORA"
    )
    columns = []
    for value in sheet.iloc[header_row, hora_column + 1 :]:
        name = _normalize(value)
        if name in ("", "TOTAL"):
            break
        columns.append(name)
    total_row = header_row + 49
    if not _normalize(sheet.iat[total_row, hora_column]).startswith("TOTAL"):
        raise ValueError(f"Expected 48 half-hours then TOTAL in the IEOD of {day}")
    rows = sheet.iloc[
        header_row + 1 : total_row, hora_column + 1 : hora_column + 1 + len(columns)
    ]
    df = pd.DataFrame(
        rows.apply(pd.to_numeric).to_numpy(),
        columns=columns,
        index=pd.date_range(
            pd.Timestamp(day, tz=TIMEZONE) + timedelta(minutes=30),
            periods=48,
            freq="30min",
        ),
    )
    return _to_modes(df, IEOD_MAP_GENERATION, logger)


def _normalize(value: object) -> str:
    """Upper case, without accents, line breaks or repeated spaces."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().upper()


if __name__ == "__main__":
    print(fetch_production())
    print(fetch_production(target_datetime=datetime(2026, 11, 8, 12, tzinfo=TIMEZONE)))
