#!/usr/bin/python3

import io
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import dateutil
import pandas as pd
import pytz

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

tz = "America/Montevideo"

MAP_GENERATION = {
    "Hidráulica": "hydro",
    "Eólica": "wind",
    "Fotovoltaica": "solar",
    "Biomasa": "biomass",
    "Térmica": "oil",
}
INV_MAP_GENERATION = dict([(v, k) for (k, v) in MAP_GENERATION.items()])

SALTO_GRANDE_URL = "http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Tensiones y Flujos de Potencia&"

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


def get_salto_grande(session: Optional[Session]) -> float:
    """Finds the current generation from the Salto Grande Dam that is allocated to Uruguay."""

    current_time = arrow.now("UTC-3")
    if current_time.minute < 30:
        # Data for current hour seems to be available after 30mins.
        current_time = current_time.shift(hours=-1)
    lookup_time = current_time.floor("hour").format("DD/MM/YYYY HH:mm")

    s = session or Session()
    url = SALTO_GRANDE_URL + lookup_time
    response = s.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tie = soup.find("div", style="position:absolute; top:143; left:597")
    generation = float(tie.text)

    return generation


def parse_page(session: Optional[Session]):
    r = session or Session()
    url = "https://apps.ute.com.uy/SgePublico/ConsPotenciaGeneracionArbolXFuente.aspx"
    response = r.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    datefield = soup.find(
        "span", attrs={"id": "ctl00_ContentPlaceHolder1_lblUltFecScada"}
    )
    datestr = re.findall("\d\d/\d\d/\d\d\d\d \d+:\d\d", str(datefield.contents[0]))[0]
    date = arrow.get(datestr, "DD/MM/YYYY h:mm").replace(tzinfo=dateutil.tz.gettz(tz))

    table = soup.find(
        "table", attrs={"id": "ctl00_ContentPlaceHolder1_gridPotenciasNivel1"}
    )

    obj = {"datetime": date.datetime}

    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not len(tds):
            continue

        key = tds[0].find_all("b")
        # Go back one level up if the b tag is not there
        if not len(key):
            key = tds[0].find_all("font")
        k = key[0].contents[0]

        value = tds[1].find_all("b")
        # Go back one level up if the b tag is not there
        if not len(value):
            value = tds[1].find_all("font")
        v_str = value[0].contents[0]
        if v_str.find(",") > -1 and v_str.find(".") > -1:
            # there can be values like "1.012,5"
            v_str = v_str.replace(".", "")
            v_str = v_str.replace(",", ".")
        else:
            # just replace decimal separator, like "125,2"
            v_str = v_str.replace(",", ".")
        v = float(v_str)

        # solar reports -0.1 at night, make it at least 0
        v = max(v, 0)

        obj[k] = v

    # https://github.com/tmrowco/electricitymap/issues/1325#issuecomment-380453296
    salto_grande = get_salto_grande(session)
    obj["Hidráulica"] = obj.get("Hidráulica", 0.0) + salto_grande

    return obj


def get_adme_url(target_datetime: datetime, session: Optional[Session] = None) -> str:
    """"""
    session = session or Session()
    next_day = target_datetime + timedelta(days=1)
    date_format = "{day}%2F{month}%2F{year}".format(
        day=target_datetime.day, month=target_datetime.month, year=target_datetime.year
    )
    next_day_format = "{day}%2F{month}%2F{year}".format(
        day=next_day.day, month=next_day.month, year=next_day.year
    )

    link = ADME_URL + date_format + "&fecha_fin=" + next_day_format + "&send=MOSTRAR"
    r = session.get(url=link)
    soup = BeautifulSoup(r.content, "html.parser")
    href_tags = soup.find_all("a", href=True)
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
    print(row.get("value"))
    if (5 >= dt.hour or dt.hour >= 20) and row.get("value") != 0:
        return 0
    else:
        return round(row.get("value"), 3)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "UY",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects production data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = arrow.utcnow().datetime
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
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(tz)),
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
        target_datetime = arrow.utcnow().datetime
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
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(tz)),
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
        target_datetime = arrow.utcnow().datetime
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
            "datetime": arrow.get(dt).datetime.replace(tzinfo=pytz.timezone(tz)),
            "source": "pronos.adme.com.uy",
        }
        all_data_points += [data_point]
    return all_data_points


# if __name__ == "__main__":
#     print("fetch_production() ->")
#     print(fetch_production())
#     print("fetch_exchange(UY, BR) ->")
#     print(fetch_exchange("UY", "BR"))
