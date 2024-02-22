#!/usr/bin/python3

import io
from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config.constants import PRODUCTION_MODES
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

UY_TZ = ZoneInfo("America/Montevideo")
UY_SOURCE = "pronos.adme.com.uy"

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
    if not r.ok:
        raise ParserException(
            parser="UY.py",
            message="Impossible to fetch data url from ADME",
        )
    soup = BeautifulSoup(r.content, "html.parser")
    href_tags = soup.find_all("a", href=True)
    data_url: str = ""
    for tag in href_tags:
        if (
            tag.button is not None
            and tag.button.string == "Archivo Scada Detalle 10minutal"
        ):
            data_url = "https://pronos.adme.com.uy" + tag.get("href")

    if not data_url:
        raise ParserException(
            parser="UY.py",
            message="Impossible to fetch data url from ADME",
        )
    return data_url


def fetch_data(
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
            message="no data available for target_datetime",
        )


def fix_solar_production(dt: datetime, value: float) -> int:
    """sets solar production to 0 during the night as there is only solar PV in UY"""
    if (dt.hour <= 5 or dt.hour >= 20) and value != 0:
        return 0
    else:
        return round(value, 3)


@refetch_frequency(timedelta(days=1))
def fetch_production(
    zone_key: str = "UY",
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects production data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = datetime.now(tz=UY_TZ)
    session = session or Session()

    production_list = ProductionBreakdownList(logger)

    data = fetch_data(
        session=session,
        target_datetime=target_datetime,
        sheet_name="GPF",
        logger=logger,
    )
    data = data.rename(columns=PRODUCTION_MODE_MAPPING)
    data = data.groupby(data.columns, axis=1).sum()
    production = data[[col for col in data.columns if col in PRODUCTION_MODES]]

    for dt, row in production.iterrows():
        production_mix = ProductionMix()
        if not row.eq(0).all() and not row.isna().all():
            for mode, value in row.items():
                if mode == "solar":
                    value = fix_solar_production(dt, value)
                production_mix.add_value(
                    mode,
                    round(float(value), 3),
                    correct_negative_with_zero=True,
                )
        production_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=dt.to_pydatetime().replace(tzinfo=UY_TZ),
            source=UY_SOURCE,
            production=production_mix,
        )

    return production_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_consumption(
    zone_key: str = "UY",
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects consumption data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = datetime.now(tz=UY_TZ)
    session = session or Session()

    consumption_list = TotalConsumptionList(logger)

    data = fetch_data(
        session=session,
        target_datetime=target_datetime,
        sheet_name="GPF",
        logger=logger,
    )
    data = data.rename(columns={"Demanda": "consumption"})

    consumption = data[["consumption"]]

    for dt, row in consumption.iterrows():
        consumption_list.append(
            zoneKey=ZoneKey(zone_key),
            datetime=dt.to_pydatetime().replace(tzinfo=UY_TZ),
            consumption=row["consumption"],
            source=UY_SOURCE,
        )

    return consumption_list.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: str,
    zone_key2: str,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """collects exchanges data from ADME and format all data points for target_datetime"""
    if target_datetime is None:
        target_datetime = datetime.now(tz=UY_TZ)
    session = session or Session()

    exchange_list = ExchangeList(logger)

    data = fetch_data(
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
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))
    exchange = data[[sorted_zone_keys]]

    for dt, row in exchange.iterrows():
        exchange_list.append(
            zoneKey=ZoneKey(sorted_zone_keys),
            datetime=dt.to_pydatetime().replace(tzinfo=UY_TZ),
            netFlow=row[sorted_zone_keys],
            source=UY_SOURCE,
        )

    return exchange_list.to_list()


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
    # print("fetch_exchange(UY, BR) ->")
    # print(fetch_exchange("UY", "BR"))
