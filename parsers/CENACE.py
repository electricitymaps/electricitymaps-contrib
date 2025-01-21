#!/usr/bin/env python3

import json
import urllib
from datetime import datetime, timedelta
from io import StringIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import tz
from requests import Response, Session

from electricitymap.contrib.config import ZONES_CONFIG
from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.config import refetch_frequency
from parsers.lib.exceptions import ParserException

CAISO_PROXY = "https://us-ca-proxy-jfnx5klx2a-uw.a.run.app"
MX_PRODUCTION_URL = f"{CAISO_PROXY}/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx?host=https://www.cenace.gob.mx"
MX_EXCHANGE_URL = f"{CAISO_PROXY}/Paginas/Publicas/Info/DemandaRegional.aspx?host=https://www.cenace.gob.mx"

EXCHANGES = {
    "MX-NO->MX-NW": "IntercambioNTE-NOR",
    "MX-NE->MX-NO": "IntercambioNES-NTE",
    "MX-NE->MX-OR": "IntercambioNES-ORI",
    "MX-OR->MX-PN": "IntercambioORI-PEN",
    "MX-CE->MX-OR": "IntercambioORI-CEL",
    "MX-OC->MX-OR": "IntercambioOCC-ORI",
    "MX-CE->MX-OC": "IntercambioOCC-CEL",
    "MX-NE->MX-OC": "IntercambioNES-OCC",
    "MX-NO->MX-OC": "IntercambioNTE-OCC",
    "MX-NW->MX-OC": "IntercambioNOR-OCC",
    "MX->US-CAL-CISO": "IntercambioUSA-BCA",
    "MX-BC->US-CAL-CISO": "IntercambioUSA-BCA",
    "MX->US-TEX-ERCO": "DummyValueNotUsed",
    "MX-NO->US-TEX-ERCO": "IntercambioUSA-NTE",
    "MX-NE->US-TEX-ERCO": "IntercambioUSA-NES",
    "BZ->MX": "IntercambioPEN-BEL",
    "BZ->MX-PN": "IntercambioPEN-BEL",
}

REGION_MAPPING = {
    "MX-BC": "BCA",
    "MX-BCS": "BCS",
    "MX-NW": "NOR",
    "MX-NO": "NTE",
    "MX-NE": "NES",
    "MX-OC": "OCC",
    "MX-CE": "CEL",
    "MX-OR": "ORI",
    "MX-PN": "PEN",
}

MAPPING = {
    "Eolica": "wind",
    "Fotovoltaica": "solar",
    "Biomasa": "biomass",
    "Carboelectrica": "coal",
    "Ciclo Combinado": "gas",
    "Geotermoelectrica": "geothermal",
    "Hidroelectrica": "hydro",
    "Nucleoelectrica": "nuclear",
    "Combustion Interna": "unknown",
    "Termica Convencional": "unknown",
    "Turbo Gas": "gas",
}
SOURCE = "cenace.gob.mx"
TIMEZONE = ZoneInfo("America/Mexico_City")

# cache where the data for whole months is stored as soon as it has been fetched once
DATA_CACHE = {}


def parse_date(date, hour):
    tzoffset = tz.tzoffset("CST", -3600 * 6)
    dt = datetime.strptime(date, "%d/%m/%Y")
    dt = dt.replace(hour=int(hour) - 1, tzinfo=tzoffset)
    return dt


def fetch_csv_for_date(dt, session: Session | None = None):
    """
    Fetches the whole month of the give datetime.
    returns the data as a DataFrame.
    throws an exception data is not available.
    """
    session = session or Session()

    response = session.get(MX_PRODUCTION_URL)
    response.raise_for_status()

    # extract necessary viewstate, validation tokens
    soup = BeautifulSoup(response.content, "html.parser")
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
    eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

    # format date string for the requested date
    datestr = dt.strftime("%m/%d/%Y")
    client_state = {"minDateStr": f"{datestr} 0:0:0", "maxDateStr": f"{datestr} 0:0:0"}

    # build parameters for POST request
    parameters = {
        "__VIEWSTATE": viewstate,
        "__EVENTVALIDATION": eventvalidation,
        "ctl00_ContentPlaceHolder1_FechaConsulta_ClientState": json.dumps(client_state),
        "ctl00$ContentPlaceHolder1$GridRadResultado$ctl00$ctl04$gbccolumn.x": "0",
        "ctl00$ContentPlaceHolder1$GridRadResultado$ctl00$ctl04$gbccolumn.y": "0",
    }

    # urlencode the data in the weird form which is expected by the API
    # plus signs MUST be contained in the date strings but MAY NOT be contained in the VIEWSTATE...
    data = urllib.parse.urlencode(parameters, quote_via=urllib.parse.quote).replace(
        "%2B0", "+0"
    )

    response = session.post(
        MX_PRODUCTION_URL,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    response.raise_for_status()

    # API returns normally status 200 but content type text/html when data is missing
    if "Content-Type" not in response.headers or "text/html" in response.headers.get(
        "Content-Type", ""
    ):
        return None

    # skip non-csv data, the header starts with "Sistema"
    csv_str = response.text
    df = pd.read_csv(
        StringIO(csv_str),
        skiprows=7,
    )

    # cleanup and parse the data
    df.columns = df.columns.str.strip()

    # transform 01-24 entries where 24 means 00 the next day
    df["Hora"] = df["Hora"].apply(lambda x: "00" if int(x) == 24 else f"{int(x):02d}")
    df["Dia"] = pd.to_datetime(df["Dia"], format="%d/%m/%Y")
    df.loc[df["Hora"] == "00", "Dia"] = df["Dia"] + pd.Timedelta(days=1)

    # The hour column has been seen at least once (3rd Nov 2024) to include 1-25
    # hours rather than the expected 1-24, due to this, we are for now dropping
    # such entries if they show up
    df = df.drop(df[df["Hora"] == "25"].index)

    # create datetime objects
    df["Dia"] = df["Dia"].dt.strftime("%d/%m/%Y")
    df["instante"] = pd.to_datetime(df["Dia"] + " " + df["Hora"], format="%d/%m/%Y %H")
    df["instante"] = df["instante"].dt.tz_localize(TIMEZONE)
    return df


def convert_production(series: pd.Series) -> ProductionMix:
    mix = ProductionMix()

    for name, val in series.items():
        name = name.strip()
        if isinstance(val, float | int):
            mix.add_value(MAPPING.get(name, "unknown"), val)

    return mix


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    if zone_key != "MX":
        raise ValueError(f"MX parser cannot fetch production for zone {zone_key}")

    if target_datetime is None:
        target_datetime = datetime.now(tz=TIMEZONE)

    original_target_datetime = target_datetime
    df = None
    up_to_months = 6  # Try up to 6 previous months
    for _ in range(up_to_months):
        cache_key = target_datetime.strftime("%Y-%m")
        if cache_key in DATA_CACHE:
            df = DATA_CACHE[cache_key]
            break
        else:
            df = fetch_csv_for_date(target_datetime, session=session)
            if df is not None and not df.empty:
                DATA_CACHE[cache_key] = df
                break
            else:
                logger.warning(f"No data found for {cache_key}. Trying previous month.")
                target_datetime = (
                    target_datetime.replace(day=1) - timedelta(days=1)
                ).replace(day=1)

    if df is None or df.empty:
        raise Exception(
            f"No data found for {original_target_datetime}, or any previous {up_to_months} months."
        )

    production = ProductionBreakdownList(logger)
    for _idx, series in df.iterrows():
        production.append(
            zoneKey=zone_key,
            datetime=series["instante"].to_pydatetime(),
            production=convert_production(series),
            source=SOURCE,
        )
    return production.to_list()


def fetch_MX_exchange(sorted_zone_keys: ZoneKey, s: Session) -> float:
    """Finds current flow between two Mexican control areas."""
    req = s.get(MX_EXCHANGE_URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(req.text, "html.parser")
    # cenace html uses unicode hyphens instead of minus signs and , as thousand separator
    trantab = str.maketrans({chr(8208): chr(45), ",": ""})
    if sorted_zone_keys == "MX->US-TEX-ERCO":
        exchange_div1 = soup.find("div", attrs={"id": "IntercambioUSA-NTE"})
        exchange_div2 = soup.find("div", attrs={"id": "IntercambioUSA-NES"})
        val1, val2 = exchange_div1.text, exchange_div2.text
        val1 = val1.translate(trantab)
        val2 = val2.translate(trantab)
        flow = float(val1) + float(val2)
    else:
        exchange_div = soup.find("div", attrs={"id": EXCHANGES[sorted_zone_keys]})
        val = exchange_div.text
        val = val.translate(trantab)
        flow = float(val)



    if sorted_zone_keys in ["BZ->MX", "BZ->MX-PN", "MX-CE->MX-OR", "MX-CE->MX-OC"]:
        # reversal needed for these zones due to EM ordering
        flow = -1 * flow

    return flow


def fetch_exchange(
    zone_key1: ZoneKey,
    zone_key2: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Requests the last known power exchange (in MW) between two zones."""
    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if sorted_zone_keys not in EXCHANGES:
        raise NotImplementedError(f"Exchange pair not supported: {sorted_zone_keys}")

    s = session or Session()

    netflow = fetch_MX_exchange(sorted_zone_keys, s)
    exchange = ExchangeList(logger)
    exchange.append(
        zoneKey=sorted_zone_keys,
        datetime=datetime.now(tz=TIMEZONE),
        netFlow=netflow,
        source=SOURCE,
    )

    return exchange.to_list()


@refetch_frequency(timedelta(hours=1))
def fetch_consumption(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    """Gets the consumption data for a region using the live dashboard."""
    # TODO the calls could be improved since we can get all the data in one call.
    if session is None:
        session = Session()
    if target_datetime is not None:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    response: Response = session.get(
        MX_EXCHANGE_URL, headers={"User-Agent": "Mozilla/5.0"}
    )
    if not response.ok:
        raise ParserException(
            "CENACE.py",
            f"[{response.status_code}] Demand dashboard could not be reached: {response.text}",
            zone_key,
        )
    soup = BeautifulSoup(response.text, "html.parser")
    demand_td = soup.find(
        "td", attrs={"id": f"Demanda{REGION_MAPPING[zone_key]}", "class": "num"}
    )
    if demand_td is None:
        raise ParserException("CENACE.py", "Could not find demand cell", zone_key)
    demand = float(demand_td.text.replace(",", ""))
    timezone = ZONES_CONFIG[zone_key].get("timezone")
    if timezone is None:
        timezone = "America/Mexico_City"
    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=datetime.now(tz=ZoneInfo(timezone)),
        consumption=demand,
        source="cenace.gob.mx",
    )
    return consumption_list.to_list()


if __name__ == "__main__":
    print(fetch_production("MX", target_datetime=datetime(year=2019, month=7, day=1)))
    print("fetch_exchange(MX-NO, MX-NW)")
    print(fetch_exchange("MX-NO", "MX-NW"))
    print("fetch_exchange(MX-OR, MX-PN)")
    print(fetch_exchange("MX-OR", "MX-PN"))
    print("fetch_exchange(MX-NE, MX-OC)")
    print(fetch_exchange("MX-NE", "MX-OC"))
    print("fetch_exchange(MX-NE, MX-NO)")
    print(fetch_exchange("MX-NE", "MX-NO"))
    print("fetch_exchange(MX-OC, MX-OR)")
    print(fetch_exchange("MX-OC", "MX-OR"))
    print("fetch_exchange(MX-NE, US-TEX-ERCO)")
    print(fetch_exchange("MX-NE", "US-TEX-ERCO"))
    print("fetch_exchange(MX-CE, MX-OC)")
    print(fetch_exchange("MX-CE", "MX-OC"))
    print("fetch_exchange(MX-PN, BZ)")
    print(fetch_exchange("MX-PN", "BZ"))
    print("fetch_exchange(MX-NO, MX-OC)")
    print(fetch_exchange("MX-NO", "MX-OC"))
    print("fetch_exchange(MX-NO, US-TEX-ERCO)")
    print(fetch_exchange("MX-NO", "US-TEX-ERCO"))
    print("fetch_exchange(MX-NE, MX-OR)")
    print(fetch_exchange("MX-NE", "MX-OR"))
    print("fetch_exchange(MX-CE, MX-OR)")
    print(fetch_exchange("MX-CE", "MX-OR"))
