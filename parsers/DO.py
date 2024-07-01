#!/usr/bin/env python3

from datetime import datetime, timedelta
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey

# This parser gets hourly electricity generation data from oc.org.do for the Dominican Republic.
# The data is in MWh but since it is updated hourly we can view it as MW.
# Solar generation now has some data available but multiple projects are planned/under construction.

DO_SOURCE = "oc.org.do"
URL = "https://apps.oc.org.do/reportesgraficos/reportepostdespacho.aspx"

TOTAL_RENEWABLES_MAPPING = {
    "Total E\xf3lico": "wind",
    "Total Hidroel\xe9ctrica": "hydro",
    "Total Solar": "solar",
}

TOTAL_MAPPING = {
    "Total T\xe9rmico": "Thermal",
    "Total Generado": "Generated",
}

# Power plant types
# http://www.sie.gob.do/images/Estadisticas/MEM/GeneracionDiariaEnero2017/
# Reporte_diario_de_generacion_31_enero_2017_merged2.pdf

THERMAL_PLANTS = {
    "AES ANDRES": "gas",
    "BARAHONA CARBON": "coal",
    "BERSAL": "oil",
    "CEPP 1": "oil",
    "CEPP 2": "oil",
    "CESPM 1 FO": "oil",
    "CESPM 1 GN": "gas",
    "CESPM 2 FO": "oil",
    "CESPM 2 GN": "gas",
    "CESPM 3 FO": "oil",
    "CESPM 3 GN": "gas",
    "ESTRELLA DEL MAR 2 CFO": "oil",
    "ESTRELLA DEL MAR 2 CGN": "gas",
    "ESTRELLA DEL MAR 2 SFO": "oil",
    "ESTRELLA DEL MAR 2 SGN": "gas",
    "ESTRELLA DEL MAR 3": "gas",
    "GENERACI\xd3N DE EMERGENCIA AES ANDR\xc9S": "gas",
    "HAINA TG": "oil",
    "INCA KM22": "oil",
    "ITABO 1": "coal",
    "ITABO 2": "coal",
    "LA VEGA": "oil",
    "LOS MINA 5": "gas",
    "LOS MINA 6": "gas",
    "LOS MINA 7": "gas",
    "LOS OR\xcdGENES POWER PLANT FUEL OIL": "oil",
    "LOS OR\xcdGENES POWER PLANT GAS NATURAL": "gas",
    "METALDOM": "oil",
    "MONTE RIO": "oil",
    "PALAMARA": "oil",
    "PALENQUE": "oil",
    "PARQUE ENERGETICO LOS MINA CC PARCIAL": "gas",
    "PARQUE ENERGETICO LOS MINA CC TOTAL": "gas",
    "PIMENTEL 1": "oil",
    "PIMENTEL 2": "oil",
    "PIMENTEL 3": "oil",
    "PUNTA CATALINA 1": "coal",
    "PUNTA CATALINA 2": "coal",
    "QUISQUEYA 1B SAN PEDRO GN": "gas",
    "QUISQUEYA 1 FO": "oil",
    "QUISQUEYA 1 GN": "gas",
    "QUISQUEYA 2 FO": "oil",
    "QUISQUEYA 2 GN": "gas",
    "QUISQUEYA 1 SAN PEDRO FO": "oil",
    "QUISQUEYA 1 SAN PEDRO GN": "gas",
    "RIO SAN JUAN": "oil",
    "SAN FELIPE": "oil",
    "SAN FELIPE CC": "gas",
    "SAN FELIPE VAP": "oil",
    "SAN LORENZO 1": "gas",
    "SAN PEDRO BIO-ENERGY": "biomass",
    "SAN PEDRO VAPOR": "oil",
    "SULTANA DEL ESTE": "oil",
}


def get_datetime_from_hour(now: datetime, hour: int) -> datetime:
    return now + timedelta(hours=int(hour) - 1)


def get_data(session: Session | None = None) -> list[list[str]]:
    """
    Makes a request to source url.
    Finds main table and creates a list of all table elements in string format.
    """

    s = session or Session()
    data_req = s.get(URL)
    soup = BeautifulSoup(data_req.content, "lxml")

    tbs = soup.find("table", id="PostdespachoUnidadesTermicasGrid_DXMainTable")
    rows = tbs.find_all("tr")

    data = []
    for row in rows:
        row_data = []
        cols = row.find_all("td")
        for col in cols:
            row_data.append(str(col.getText().strip()))
        data.append(row_data)

    return data


def floater(item):
    """
    Attempts to convert any item given to a float.
    Returns item if it fails.
    """

    try:
        return float(item)
    except ValueError:
        return item


def chunker(big_lst) -> dict:
    """
    Breaks a big list into a list of lists.
    Removes any list with no data then turns remaining
    lists into key: value pairs with first element from the list being the key.
    """

    chunks = [big_lst[x : x + 27] for x in range(0, len(big_lst), 27)]

    # Remove the list if it contains no data.
    for chunk in chunks:
        if any(chunk):
            continue
        else:
            chunks.remove(chunk)

    chunked_list = {words[0]: words[1:] for words in chunks}

    return chunked_list


def data_formatter(data: list[list[str]]) -> list[list[str]]:
    """
    Aligns the tabular data to a standard format: (ID, hour_0, hour_1, ... , hour_23, hour_24)
    """

    INIT_ROWS_TO_DROP = 26
    data = data[INIT_ROWS_TO_DROP:]

    def format_row(row: list[str]) -> list[str]:
        # Case Grupo: X
        match_grupo = len(row) == 2 and row[0] == "" and "grupo" in row[1].lower()
        # Case Empresa: X
        match_empresa = (
            len(row) == 3
            and all(c == "" for c in row[:2])
            and "empresa" in row[2].lower()
        )
        # Case Unit: X
        match_unit = len(row) == 27 and all(c == "" for c in row[:2])

        if match_grupo:
            return [row[1]] + [""] * 24
        elif match_empresa:
            return [row[2]] + [""] * 24
        elif match_unit:
            return row[2:]
        else:
            raise ValueError(f"Unexpected row format: {row}")

    data = [format_row(row) for row in data]
    return data


def correct_solar_production(production: pd.DataFrame) -> pd.DataFrame:
    """
    Solar production is not reported when it's zero.
    """
    if production.solar.isnull().all() or production.solar.notnull().all():
        return production
    production = production.copy()
    null_production_index = production[production.solar.isnull()].index
    max_non_null_solar_idx = production.solar.last_valid_index()
    indices_to_set_to_zero = [
        idx for idx in null_production_index if idx < max_non_null_solar_idx
    ]
    # Replace all NaN values with 0 up to the first non-null value
    production.loc[indices_to_set_to_zero] = 0
    return production


def extract_renewable_production(data: list[list[str]], dt: datetime) -> pd.DataFrame:
    """
    Extract renewable production data from the total rows.
    """
    renewable_indices = [
        i for i, row in enumerate(data) if row[0] in TOTAL_RENEWABLES_MAPPING
    ]
    renewable_data = []
    for i in renewable_indices:
        row = data[i]
        renewable_data.append([TOTAL_RENEWABLES_MAPPING[row[0]]] + row[1:])
    df = pd.DataFrame(renewable_data, columns=["mode"] + list(range(1, 25)))
    # pivot to have hours as index and mode as columns
    df = df.set_index("mode").T
    df.index = [get_datetime_from_hour(dt, hour) for hour in df.index]
    df.index.name = "datetime"
    # Convert to numeric
    df = df.apply(pd.to_numeric)
    df = correct_solar_production(df)
    return df


def extract_thermal_production(data: list[list[str]], dt: datetime) -> pd.DataFrame:
    """
    Extract thermal production from individual power plants.
    """
    thermal_indices = [i for i, row in enumerate(data) if row[0] in THERMAL_PLANTS]
    thermal_data = []
    for i in thermal_indices:
        row = data[i]
        thermal_data.append([THERMAL_PLANTS.get(row[0], "unknown")] + row[1:])
    df = pd.DataFrame(thermal_data, columns=["mode"] + list(range(1, 25)))
    # Convert numeric
    df = df.apply(pd.to_numeric, errors="ignore")
    # Group by sum per mode
    df = df.groupby("mode").sum(min_count=1)
    # pivot to have hours as index and mode as columns
    df = df.T
    df.index = [get_datetime_from_hour(dt, hour) for hour in df.index]
    df.index.name = "datetime"
    return df


def fetch_production(
    zone_key: ZoneKey = ZoneKey("DO"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    now = datetime.now(tz=ZoneInfo("America/Dominica")).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    data = data_formatter(get_data(session=session))
    renewable_production = extract_renewable_production(data, now)
    thermal_production = extract_thermal_production(data, now)
    production = pd.concat([renewable_production, thermal_production], axis=1)
    # only keep rows with at least one non-null value
    production = production.dropna(how="all")

    production_list = ProductionBreakdownList(logger)
    for ts, mix in production.iterrows():
        production_mix = ProductionMix(**mix.to_dict())
        production_list.append(
            zoneKey=zone_key,
            datetime=ts.to_pydatetime(),
            source=DO_SOURCE,
            production=production_mix,
        )

    return production_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
