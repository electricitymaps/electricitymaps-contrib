#!/usr/bin/env python3

import json
import re
import urllib
from datetime import datetime, date, timedelta
from io import StringIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from dateutil import tz
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

MX_PRODUCTION_URL = (
    "https://www.cenace.gob.mx/Paginas/SIM/Reportes/EnergiaGeneradaTipoTec.aspx"
)
MX_EXCHANGE_URL = "https://www.cenace.gob.mx/Paginas/Publicas/Info/DemandaRegional.aspx"

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
MONTH_NAMES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}
MONTH_MAP = dict(map(reversed, MONTH_NAMES.items()))
SOURCE = "cenace.gob.mx"
TIMEZONE = ZoneInfo("America/Mexico_City")

# cache where the data for whole months is stored as soon as it has been fetched once
DATA_CACHE = {}


def fetch_csv_for_date(dt, session: Session | None = None):
    """
    Fetches the whole month of the give datetime.
    returns the data as a DataFrame.
    throws an exception data is not available.
    """
    session = session or Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    response = session.get(MX_PRODUCTION_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    parsed_date = parse_month_from_html(soup)

    dt = dt.date().replace(day=1)

    if parsed_date < dt:
        raise Exception(
            f"{dt} has no data yet, try {parsed_date}"
        )
    elif parsed_date > dt:
        datestr = dt.strftime("%m/%d/%Y")
        client_state = {"minDateStr": f"{datestr}+0:0:0", "maxDateStr": f"{datestr}+0:0:0"}
        parameters = {
            "ctl00$ContentPlaceHolder1$ScriptManager1": "ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$FechaConsulta",
            "ctl00_ContentPlaceHolder1_FechaConsulta_AD": json.dumps([["2016-04-30", 4, 30], [2025, 1, 1], [2025, 1, 1]]),
            "ctl00$ContentPlaceHolder1$FechaConsulta": dt.strftime("%Y-%m-%d"),
            "ctl00$ContentPlaceHolder1$FechaConsulta$dateInput": f"{MONTH_NAMES[dt.month]}+de+{dt.year}",
            "ctl00_ContentPlaceHolder1_FechaConsulta_ClientState": json.dumps(client_state),
            "ctl00_ContentPlaceHolder1_FechaConsulta_dateInput_ClientState": json.dumps({
                "enabled": True,
                "emptyMessage": "",
                "validationText": f"{dt.strftime('%Y-%m-%d')}-00-00-00",
                "valueAsString": f"{dt.strftime('%Y-%m-%d')}-00-00-00",
                "minDateStr": "2016-04-30-00-00-00",
                "maxDateStr": "2025-11-16-00-00-00",
                "lastSetTextBoxValue": f"{MONTH_NAMES[dt.month]}+de+{dt.year}"
            }),
        }

        response = submit_form(session, soup, parameters)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        parsed_date = parse_month_from_html(soup)

        if parsed_date != dt:
            raise ParserException(
                "CENACE.py",
                f"request returned wrong date {parsed_date} expected {dt}"
            )


    pattern = re.compile(
        r"^ctl00\$ContentPlaceHolder1\$GridRadResultado\$ctl00\$ctl\d+\$gbccolumn$"
    )
    image_inputs = soup.find_all("input", {"type": "image", "name": pattern})
    button_name = image_inputs[-1]["name"]
    parameters = {
        f"{button_name}.x": "0",
        f"{button_name}.y": "0"
    }

    response = submit_form(session, soup, parameters)

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


def submit_form(
    session: Session,
    soup: BeautifulSoup,
    parameters,
) -> Response:
    # Extract VIEWSTATE and EVENTVALIDATION from the HTML
    viewstate = soup.find("input", {"name": "__VIEWSTATE"})["value"]
    viewstate_generator = soup.find("input", {"name": "__VIEWSTATEGENERATOR"})["value"]
    eventvalidation = soup.find("input", {"name": "__EVENTVALIDATION"})["value"]

    # Build form parameters
    parameters.update({
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": viewstate_generator,
        "__EVENTVALIDATION": eventvalidation,
    })

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

    return response


def parse_month_from_html(soup: BeautifulSoup) -> datetime.date:
    text = soup.select_one('#ctl00_ContentPlaceHolder1_GridRadResultado_ctl00 tbody tr td')
    month, year = text.get_text(strip=True).split()

    return date(int(year), MONTH_MAP[month], 1)


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

    cache_key = target_datetime.strftime("%Y-%m")

    # Check cache first
    if cache_key in DATA_CACHE:
        df = DATA_CACHE[cache_key]
    else:
        df = fetch_csv_for_date(target_datetime, session)
        DATA_CACHE[cache_key] = df

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
    if zone_key == "MX-BC" or zone_key == "MX-BCS":
        timezone = "America/Tijuana"
    else:
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
    print(
        fetch_production(
            ZoneKey("MX"), target_datetime=datetime(year=2019, month=7, day=1)
        )
    )
    print("fetch_exchange(MX-NO, MX-NW)")
    print(fetch_exchange(ZoneKey("MX-NO"), ZoneKey("MX-NW")))
    print("fetch_exchange(MX-OR, MX-PN)")
    print(fetch_exchange(ZoneKey("MX-OR"), ZoneKey("MX-PN")))
    print("fetch_exchange(MX-NE, MX-OC)")
    print(fetch_exchange(ZoneKey("MX-NE"), ZoneKey("MX-OC")))
    print("fetch_exchange(MX-NE, MX-NO)")
    print(fetch_exchange(ZoneKey("MX-NE"), ZoneKey("MX-NO")))
    print("fetch_exchange(MX-OC, MX-OR)")
    print(fetch_exchange(ZoneKey("MX-OC"), ZoneKey("MX-OR")))
    print("fetch_exchange(MX-NE, US-TEX-ERCO)")
    print(fetch_exchange(ZoneKey("MX-NE"), ZoneKey("US-TEX-ERCO")))
    print("fetch_exchange(MX-CE, MX-OC)")
    print(fetch_exchange(ZoneKey("MX-CE"), ZoneKey("MX-OC")))
    print("fetch_exchange(MX-PN, BZ)")
    print(fetch_exchange(ZoneKey("MX-PN"), ZoneKey("BZ")))
    print("fetch_exchange(MX-NO, MX-OC)")
    print(fetch_exchange(ZoneKey("MX-NO"), ZoneKey("MX-OC")))
    print("fetch_exchange(MX-NO, US-TEX-ERCO)")
    print(fetch_exchange(ZoneKey("MX-NO"), ZoneKey("US-TEX-ERCO")))
    print("fetch_exchange(MX-NE, MX-OR)")
    print(fetch_exchange(ZoneKey("MX-NE"), ZoneKey("MX-OR")))
    print("fetch_exchange(MX-CE, MX-OR)")
    print(fetch_exchange(ZoneKey("MX-CE"), ZoneKey("MX-OR")))
