#!/usr/bin/env python3
# coding=utf-8

import json
import logging
import re

import arrow
import pandas as pd
import requests
from bs4 import BeautifulSoup

TIMEZONE = "America/Panama"

EXCHANGE_URL = "https://sitr.cnd.com.pa/m/pub/int.html"
CONSUMPTION_URL = "https://sitr.cnd.com.pa/m/pub/sin.html"
PRODUCTION_URL = "https://sitr.cnd.com.pa/m/pub/gen.html"

# Sources:
# 1. https://www.celsia.com/Portals/0/contenidos-celsia/accionistas-e-inversionistas/perfil-corporativo-US/presentaciones-US/2014/presentacion-morgan-ingles-v2.pdf
# 2. https://www.celsia.com/en/about-celsia/business-model/power-generation/thermoelectric-power-plants
# 3. https://endcoal.org/tracker/
# 4. http://aesmcac.com/aespanamades/en/colon/ "It reuses the heat from the exhaust gas from the gas turbines in order to obtain steam, to be later used by a steam turbine and to save fuel consumption in the production of electricity."
# 5. https://panamcham.com/sites/default/files/el_inicio_del_futuro_del_gas_natural_en_panama.pdf "3 gas turbines and 1 steam (3X1 configuration)" "Technology: Combined Cycle" | This and the previous source taken together seems to imply that the steam turbine is responsible for the second cycle of the CCGT plant, giving confidence that output from all four units should indeed be tallied under "gas". Furthermore, as the plant also has a LNG import facility it is most unlikely the steam turbine would be burning a different fuel such as coal or oil.
# 6. https://www.etesa.com.pa/documentos/Tomo_II__Plan_Indicativo_de_Generacin_2019__2033.pdf page 142
# 7. http://168.77.210.79/energia/wp-content/uploads/sites/2/2020/08/2-CEE-1970-2019-GE-Generaci%C3%B3n-El%C3%A9ctrica.xls (via http://www.energia.gob.pa/mercado-energetico/?tag=84#documents-list)
# 8. https://www.asep.gob.pa/wp-content/uploads/electricidad/resoluciones/anno_12528_elec.pdf
# 9. https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2018/May/IRENA_RRA_Panama_2018_En.pdf
# 10. https://www.asep.gob.pa/wp-content/uploads/electricidad/concesiones_licencias/concesiones_licencias/2021/listado_licencias_abr27.pdf
MAP_THERMAL_GENERATION_UNIT_NAME_TO_FUEL_TYPE = {
    "ACP Miraflores 2": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 5": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 6": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 7": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 8": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 9": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "ACP Miraflores 10": "oil",  # [7] Sheet "C-GE-1A-1 CapInstXEmp"
    "BLM 2": "coal",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 3": "coal",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 4": "coal",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 5": "oil",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 6": "oil",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 8": "oil",  # [7] Sheet "C-GE-1A-2 CapInstXEmp"
    "BLM 9": "oil",  # [7] Sheet "C-GE-1A-2 CapInstXEmp" mentions no fuel type, and given all other units are accounted for this must be the heat recovery boiler for the 3 diesel-fired units mentioned in [2]
    "CADASA 1": "biomass",  # [9]
    "CADASA 2": "biomass",  # [9]
    "Cativá 1": "oil",  # [1][2]
    "Cativá 2": "oil",  # [1][2]
    "Cativá 3": "oil",  # [1][2]
    "Cativá 4": "oil",  # [1][2]
    "Cativá 5": "oil",  # [1][2]
    "Cativá 6": "oil",  # [1][2]
    "Cativá 7": "oil",  # [1][2]
    "Cativá 8": "oil",  # [1][2]
    "Cativá 9": "oil",  # [1][2]
    "Cativá 10": "oil",  # [1][2]
    "Cobre Panamá 1": "coal",  # [3]
    "Cobre Panamá 2": "coal",  # [3]
    "Costa Norte 1": "gas",  # [4][5]
    "Costa Norte 2": "gas",  # [4][5]
    "Costa Norte 3": "gas",  # [4][5]
    "Costa Norte 4": "gas",  # [4][5]
    "Esperanza 1": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 2": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 3": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 4": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 5": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 6": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Esperanza 7": "oil",  # [7] has a single 92MW bunker fuel power plant, but [8] shows this is actually a power barge with 7 units
    "Jinro": "oil",  # [6][7]
    "Pacora 1": "oil",  # [6]
    "Pacora 2": "oil",  # [6]
    "Pacora 3": "oil",  # [6]
    "PanAm 1": "oil",  # [6][7]
    "PanAm 2": "oil",  # [6][7]
    "PanAm 3": "oil",  # [6][7]
    "PanAm 4": "oil",  # [6][7]
    "PanAm 5": "oil",  # [6][7]
    "PanAm 6": "oil",  # [6][7]
    "PanAm 7": "oil",  # [6][7]
    "PanAm 8": "oil",  # [6][7]
    "PanAm 9": "oil",  # [6][7]
    "Sparkle Power 1": "oil",  # [10]
    "Sparkle Power 2": "oil",  # [10]
    "Sparkle Power 3": "oil",  # [10]
    "Sparkle Power 4": "oil",  # [10]
    "Sparkle Power 5": "oil",  # [10]
    "Sparkle Power 6": "oil",  # [10]
    "Sparkle Power 7": "oil",  # [10]
    "Sparkle Power 8": "oil",  # [10]
    "Termocolón 1": "oil",  # [6] (spelled "Termo Colón")
    "Termocolón 2": "oil",  # [6] (spelled "Termo Colón")
    "Termocolón 3": "oil",  # [6] (spelled "Termo Colón")
    "Tropitérmica 1": "oil",  # [6]:162[7] spelled "Tropitermica" in both
    "Tropitérmica 2": "oil",  # [6]:162[7] spelled "Tropitermica" in both
    "Tropitérmica 3": "oil",  # [6]:162[7] spelled "Tropitermica" in both
}


def extract_pie_chart_data(html):
    """Extracts generation breakdown pie chart data from the source code of the page"""
    data_source = re.search(r"var localPie = (\[\{.+\}\]);", html).group(
        1
    )  # Extract object with data
    data_source = re.sub(
        r"(name|value|color)", r'"\1"', data_source
    )  # Un-quoted keys ({key:"value"}) are valid JavaScript but not valid JSON (which requires {"key":"value"}). Will break if other keys than these three are introduced. Alternatively, use a JSON5 library (JSON5 allows un-quoted keys)
    return json.loads(data_source)


def sum_thermal_units(soup) -> float:
    """
    Sums thermal units of the generation mix to prevent using slightly outdated chart data.

    Thermal total from the graph and the total one would get from summing output of all generators deviates a bit,
    presumably because they aren't updated at the exact same moment.
    """

    thermal_h3 = soup.find("h3", string=re.compile(r"\s*Térmicas\s*"))
    thermal_tables = thermal_h3.find_next_sibling().find_all(
        "table", {"class": "table table-hover table-striped table-sm sitr-gen-group"}
    )

    thermal_units = 0

    for thermal_table in thermal_tables:
        thermal_units += sum(
            [
                float(span.text)
                for span in thermal_table.find_all("span", {"style": "color:#222"})
            ]
        )
        thermal_units += sum(
            [
                float(span.text)
                for span in thermal_table.find_all("span", {"style": "color:ROYALBLUE"})
            ]
        )

    return thermal_units


def fetch_production(
    zone_key="PA",
    session=None,
    target_datetime=None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # Fetch page and load into BeautifulSoup
    r = session or requests.session()
    url = PRODUCTION_URL
    response = r.get(url)
    response.encoding = "utf-8"
    html_doc = response.text
    soup = BeautifulSoup(html_doc, "html.parser")

    # Parse production from pie chart
    productions = extract_pie_chart_data(
        html_doc
    )  # [{name:"Hídrica 1342.54 (80.14%)",value:1342.54,color:"#99ccee"}, ...]

    # Sum thermal units from table Térmicas (MW)
    thermal_sum = sum_thermal_units(soup)

    map_generation = {
        "Hídrica": "hydro",
        "Eólica": "wind",
        "Solar": "solar",
        "Biogás": "biomass",
        "Térmica": "unknown",
    }
    data = {
        "zoneKey": "PA",
        "production": {
            # Setting default values here so we can do += when parsing the thermal generation breakdown
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "nuclear": 0.0,
            "oil": 0.0,
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "unknown": 0.0,
        },
        "storage": {},
        "source": "https://www.cnd.com.pa/",
    }
    for prod in productions:  # {name:"Hídrica 1342.54 (80.14%)", ...}
        prod_data = prod["name"].split(" ")  # "Hídrica 1342.54 (80.14%)"
        production_type = map_generation[prod_data[0]]  # Hídrica
        production_value = float(prod_data[1])  # 1342.54
        data["production"][production_type] = production_value

    # Replacing chart termica data with manually calculated thermal generation to avoid using outdated chart data
    data["production"]["unknown"] = thermal_sum

    # Known fossil plants: parse, subtract from "unknown", add to "coal"/"oil"/"gas"
    thermal_production_breakdown = soup.find_all("table", {"class": "sitr-table-gen"})[
        1
    ]
    # Make sure the table header is indeed "Térmicas (MW)" (in case the tables are re-arranged)
    thermal_production_breakdown_table_header = (
        thermal_production_breakdown.parent.parent.parent.select("> .tile-title")[
            0
        ].string
    )
    assert "Térmicas" in thermal_production_breakdown_table_header, (
        "Exception when extracting thermal generation breakdown for {}: table header does not contain "
        "'Térmicas' but is instead named {}".format(
            zone_key, thermal_production_breakdown_table_header
        )
    )
    thermal_production_units = thermal_production_breakdown.select(
        "tbody tr td table.sitr-gen-group tr"
    )

    for thermal_production_unit in thermal_production_units:
        unit_name_and_generation = thermal_production_unit.find_all("td")
        unit_name = unit_name_and_generation[0].string
        unit_generation = float(unit_name_and_generation[1].string)
        if unit_name in MAP_THERMAL_GENERATION_UNIT_NAME_TO_FUEL_TYPE:
            if unit_generation > 0:  # Ignore self-consumption
                unit_fuel_type = MAP_THERMAL_GENERATION_UNIT_NAME_TO_FUEL_TYPE[
                    unit_name
                ]
                data["production"][unit_fuel_type] += unit_generation
                data["production"]["unknown"] -= unit_generation
        else:
            logger.warning(
                "{} is not mapped to generation type".format(unit_name),
                extra={"key": zone_key},
            )

    if 0 > data["production"]["unknown"] > -10:
        logger.info(
            f"Ignoring small amount of negative thermal generation ({data['production']['unknown']}MW)",
            extra={"key": zone_key},
        )
        data["production"]["unknown"] = 0.0

    # Round remaining "unknown" output to 13 decimal places to get rid of floating point errors
    data["production"]["unknown"] = round(data["production"]["unknown"], 13)

    if 0 < data["production"]["unknown"] < 1e-3:
        data["production"]["unknown"] = 0.0

    # Parse the datetime and return a python datetime object
    spanish_date = soup.find("h3", {"class": "sitr-update"}).string
    date = arrow.get(
        spanish_date, "DD-MMMM-YYYY H:mm:ss", locale="es", tzinfo="America/Panama"
    )
    data["datetime"] = date.datetime

    return data


def fetch_exchange(
    zone_key1="CR",
    zone_key2="PA",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """
    Requests the last known power exchange (in MW) between two countries.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    r = session or requests.session()
    url = EXCHANGE_URL

    response = r.get(url)
    assert response.status_code == 200

    df = pd.read_html(response.text)[0]

    # A positive value on website indicates a flow from country specified to PA.
    net_flow_cr = round(
        float(df[4][1])
        + float(df[4][3])
        + float(df[4][5])
        + float(df[1][8])
        + float(df[1][10]),
        2,
    )
    net_flow_gt = round(
        float(df[4][23]) + float(df[4][26]) + float(df[4][28]) + float(df[1][31]), 2
    )
    net_flow_hn = round(
        float(df[1][13])
        + float(df[1][15])
        + float(df[1][18])
        + float(df[1][20])
        + float(df[1][23]),
        2,
    )
    net_flow_ni = round(
        float(df[4][8]) + float(df[4][10]) + float(df[4][13]) + float(df[4][15]), 2
    )

    # invert sign to account for direction in alphabetical order
    net_flow_sv = -1 * round(
        float(df[4][18]) + float(df[4][20]) + float(df[1][26]) + float(df[1][28]), 2
    )

    net_flows = {
        "CR->PA": net_flow_cr,  # Costa Rica to Panama
        "GT->PA": net_flow_gt,  # Guatemala to Panama
        "HN->PA": net_flow_hn,  # Honduras to Panama
        "NI->PA": net_flow_ni,  # Nicaragua to Panama
        "PA->SV": net_flow_sv,  # Panama to El Salvador
    }

    if sorted_zone_keys not in net_flows:
        raise NotImplementedError(
            f"This exchange pair is not implemented: {sorted_zone_keys}"
        )

    data = {
        "datetime": arrow.now(TIMEZONE).datetime,
        "netFlow": net_flows[sorted_zone_keys],
        "sortedZoneKeys": sorted_zone_keys,
        "source": url,
    }

    return data


def fetch_consumption(
    zone_key="PA",
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
) -> dict:
    """
    Fetches consumption of Panama.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    r = session or requests.session()
    url = CONSUMPTION_URL

    response = r.get(url)
    assert response.status_code == 200

    soup = BeautifulSoup(response.text, "html.parser")
    consumption_title = soup.find("h5", string=re.compile(r"\s*Demanda Total\s*"))
    consumption_val = float(consumption_title.find_next_sibling().text.split()[0])

    data = {
        "consumption": consumption_val,
        "datetime": arrow.now(TIMEZONE).datetime,
        "source": url,
        "zoneKey": zone_key,
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_exchange() ->")
    print(fetch_exchange())
    print("fetch_consumption() ->")
    print(fetch_consumption())
