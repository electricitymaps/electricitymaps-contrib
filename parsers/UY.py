#!/usr/bin/python3

import io
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import pandas as pd
import pytz

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

UY_TZ = "America/Montevideo"

ADME_URL = "https://pronos.adme.com.uy/gpf.php?fecha_ini="
PRODUCTION_MODE_MAPPING = {
    "Salto Grande": "hydro",
    "Bonete": "hydro",
    "Baygorria": "hydro",
    "Palmar": "hydro",
    "Eólica": "wind",
    "Solar": "solar",
    "Térmica": "oil",
    "Biomasa": "biomass",
}
EXCHANGES_MAPPING = {
    "Exp_Intercon_ARG": "AR->UY",
    "Exp_Intercon_BR_MELO": "BR-S->UY",
    "Exp_Intercon_BR_RIVERA": "BR-S->UY",
    "Imp_Intercon_AG_Imp": "AR->UY",
    "Imp_Intercon_BR_MELO": "BR-S->UY",
    "Imp_Intercon_BR_RIVERA": "BR-S->UY",
}


def get_adme_url(target_datetime: datetime, session: Session) -> str:
    """"""
    next_day = target_datetime + timedelta(days=1)
    date_format = (
        f"{target_datetime.day}%2F{target_datetime.month}%2F{target_datetime.year}"
    )
    next_day_format = f"{next_day.day}%2F{next_day.month}%2F{next_day.year}"

    link = f"{ADME_URL}{date_format}&fecha_fin={next_day_format}&send=MOSTRAR"
    r = session.get(url=link)
    soup = BeautifulSoup(r.content, "html.parser")
    href_tags = soup.find_all("a", href=True)
    data_url: str = ""
    for tag in href_tags:
        if tag.button is not None:
            if tag.button.string == "Archivo Scada Detalle 10minutal":
                data_url = "https://pronos.adme.com.uy" + tag.get("href")
    return data_url


def fetch_data(
    zone_key: str,
    session: Session,
    target_datetime: datetime,
    sheet_name: str,
    logger: Logger = getLogger(__name__),
) -> pd.DataFrame:
    """ """
    assert target_datetime is not None
    assert session is not None
    assert sheet_name != "" or sheet_name is not None
    adme_url = get_adme_url(target_datetime=target_datetime, session=session)
    r = session.get(url=adme_url)
    if r.status_code == 200:
        df_data = pd.read_excel(
            io.BytesIO(r.content), engine="odf", header=2, sheet_name=sheet_name
        )
        df_data.columns = df_data.columns.str.strip()
        df_data = df_data.rename(columns={"Fecha": "datetime"})

        df_data = df_data.set_index("datetime")
        return df_data
    else:
        raise ParserException(
            parser="UY.py",
            message="no data available for target_dateitme",
        )


def fix_solar_production(dt: datetime, row: pd.Series) -> int:
    """sets solar production to 0 during the night as there is only solar PV in UY"""
    if (5 >= dt.hour or dt.hour >= 20) and row.get("value") != 0:
        return 0
    else:
        return round(row.get("value"), 3)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "UY",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects production data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().replace(tzinfo=UY_TZ).datetime
    session = session or Session()

    data = fetch_data(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        sheet_name="GPF",
        logger=logger,
    )
    data = data.rename(columns=PRODUCTION_MODE_MAPPING)
    data = data.groupby(data.columns, axis=1).sum()
    production = data[[col for col in data.columns if col in PRODUCTION_MODES]]
    production = pd.melt(production, var_name="production_mode", ignore_index=False)
    all_data_points = []
    for dt in production.index.unique():
        production_dict = {}
        data_dt = production.loc[production.index == dt]
        for i in range(len(data_dt)):
            row = data_dt.iloc[i]
            mode = row["production_mode"]
            if mode == "solar":
                production_dict[mode] = fix_solar_production(dt=dt, row=row)
            else:
                production_dict[mode] = round(row.get("value"), 3)
        data_point = {
            "zoneKey": "UY",
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(UY_TZ)),
            "production": production_dict,
            "source": "pronos.adme.com.uy",
        }
        all_data_points += [data_point]
    return all_data_points


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "UY",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects consumption data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().replace(tzinfo=UY_TZ).datetime
    session = session or Session()

    data = fetch_data(
        zone_key=zone_key,
        session=session,
        target_datetime=target_datetime,
        sheet_name="GPF",
        logger=logger,
    )
    data = data.rename(columns={"Demanda": "consumption"})

    consumption = data[["consumption"]].to_dict(orient="index")
    all_data_points = []
    for dt in consumption:
        data_point = {
            "zoneKey": "UY",
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(UY_TZ)),
            "consumption": round(consumption[dt]["consumption"], 3),
            "source": "pronos.adme.com.uy",
        }
        all_data_points += [data_point]
    return all_data_points


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects exchanges data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().replace(tzinfo=UY_TZ).datetime
    session = session or Session()

    data = fetch_data(
        zone_key=zone_key1,
        session=session,
        target_datetime=target_datetime,
        sheet_name="Intercambios.",
        logger=logger,
    )
    data.loc[:, data.columns.str.contains("Exp_")] = -data.loc[
        :, data.columns.str.contains("Exp_")
    ]

    data = data.rename(columns=EXCHANGES_MAPPING)
    data = data.groupby(data.columns, axis=1).sum()
    sortedZoneKeys = "->".join(sorted([zone_key1, zone_key2]))
    exchange = data[[sortedZoneKeys]].to_dict(orient="index")
    all_data_points = []
    for dt in exchange:
        data_point = {
            "netFlow": round(exchange[dt][sortedZoneKeys], 3),
            "sortedZoneKeys": sortedZoneKeys,
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(UY_TZ)),
            "source": "pronos.adme.com.uy",
        }
        all_data_points += [data_point]
    return all_data_points


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    # print("fetch_exchange(UY, BR) ->")
    # print(fetch_exchange("UY", "BR"))
