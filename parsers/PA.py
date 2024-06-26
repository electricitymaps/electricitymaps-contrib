import re
from datetime import datetime
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    TotalConsumptionList,
)
from electricitymap.contrib.lib.models.events import ProductionMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

PARSER = "PA.py"
TIMEZONE = ZoneInfo("America/Panama")
ZONE_KEY = ZoneKey("PA")

CONSUMPTION_URL = "https://sitr.cnd.com.pa/m/pub/data/sin.json"
CONSUMPTION_SOURCE = "sitr.cnd.com.pa"

EXCHANGE_URL = "https://sitr.cnd.com.pa/m/pub/data/int.json"
EXCHANGE_SOURCE = "sitr.cnd.com.pa"

PRODUCTION_URL = "https://sitr.cnd.com.pa/m/pub/data/gen.json"
PRODUCTION_SOURCE = "sitr.cnd.com.pa"

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

PRODUCTION_TYPE_TO_PRODUCTION_MODE = {
    "Hídrica": "hydro",
    "Eólica": "wind",
    "Solar": "solar",
    "Biogás": "biomass",
    "Térmica": "unknown",
}

COUNTRY_TO_EXCHANGE_NODES = {
    "PA": {"Changuinola", "Dominical", "Progreso"},
    "CR": {"Cahuita", "Canas", "Liberia", "Río Claro"},
    "NI": {"Amayo", "León", "Sandino", "Ticuantepe"},
    "HN": {"Agua Caliente", "Aguas Cal.", "La Entrada", "Los Prados", "Nacaome"},
    "SV": {"15 Sept.", "Ahuachapan"},
    "GT": {"Brillantes", "Las Vegas 2", "Moyuta", "Panaluya"},
}

_SPANISH_CALENDAR = {
    "enero": "01",
    "febrero": "02",
    "marzo": "03",
    "abril": "04",
    "mayo": "05",
    "junio": "06",
    "julio": "07",
    "agosto": "08",
    "septiembre": "09",
    "octubre": "10",
    "noviembre": "11",
    "diciembre": "12",
}


def _localise_spanish_date(date: str) -> str:
    """Localises a date containing full name (lowercase) spanish months, replacing them with zero-padded decimal numbers.

    This avoids having to mess up the global locale to be able to parse the date.
    """
    return re.sub(
        "|".join(_SPANISH_CALENDAR.keys()),
        lambda m: _SPANISH_CALENDAR[m.group(0)],
        date,
    )


def fetch_production(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known production mix (in MW) of a given country."""

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    # Fetch page and load into BeautifulSoup
    r = session or Session()
    response = r.get(PRODUCTION_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    response_payload = response.json()

    # Parse the datetime and return a python datetime object
    spanish_date = response_payload["update"]
    english_date = _localise_spanish_date(spanish_date)
    date = datetime.strptime(english_date, "%d-%m-%Y %H:%M:%S").replace(tzinfo=TIMEZONE)

    production_mix = ProductionMix()
    productions = response_payload["pie"]
    # [{name:"Hídrica 1342.54 (80.14%)",value:1342.54,color:"#99ccee"}, ...]
    for production in productions:  # {name:"Hídrica 1342.54 (80.14%)", ...}
        production_type, production_value, _percentage = production["name"].split(
            " ", 2
        )
        # ignore termica data to avoid using outdated chart data
        if production_type == "Térmica":
            continue
        production_mode = PRODUCTION_TYPE_TO_PRODUCTION_MODE[production_type]  # hydro
        production_mix.add_value(production_mode, float(production_value))

    # calculate our own 'termica' data by summing known fossil plants and bucketing into "coal"/"oil"/"gas"
    production_units = response_payload["unit"]
    for production_unit in production_units:
        unit_name = production_unit["name"]
        unit_generation = float(production_unit["value"])
        if (
            unit_name in MAP_THERMAL_GENERATION_UNIT_NAME_TO_FUEL_TYPE
            and unit_generation >= 0
        ):  # Ignore self-consumption
            unit_fuel_type = MAP_THERMAL_GENERATION_UNIT_NAME_TO_FUEL_TYPE[unit_name]
            production_mix.add_value(unit_fuel_type, unit_generation)

    production_breakdown_list = ProductionBreakdownList(logger)
    production_breakdown_list.append(
        zoneKey=zone_key,
        datetime=date,
        source=PRODUCTION_SOURCE,
        production=production_mix,
    )
    return production_breakdown_list.to_list()


def fetch_exchange(
    zone_key1: ZoneKey = ZONE_KEY,
    zone_key2: ZoneKey = ZoneKey("CR"),
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the last known power exchange (in MW) between two countries."""

    sorted_zone_keys = ZoneKey("->".join(sorted([zone_key1, zone_key2])))

    if target_datetime is not None:
        raise ParserException(
            PARSER,
            "This parser is not yet able to parse historical data",
            sorted_zone_keys,
        )

    session = session or Session()
    timestamp = datetime.now(tz=TIMEZONE)
    response = session.get(EXCHANGE_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            sorted_zone_keys,
        )

    response_payload = response.json()
    nodes = response_payload["nodes"]
    nodes_flattened = [node["from"] for node in nodes] + [node["to"] for node in nodes]

    net_flows = {}
    for country in COUNTRY_TO_EXCHANGE_NODES:
        net_flow_country = sum(
            float(n["mw"])
            for n in nodes_flattened
            if n["name"] in COUNTRY_TO_EXCHANGE_NODES[country]
        )

        # insert net flow taking into account alphabetical sorting of zone keys
        sorted_exchange_key = ZoneKey("->".join(sorted([country, "PA"])))
        net_flows[sorted_exchange_key] = (
            net_flow_country
            if sorted_exchange_key.endswith("PA")
            else -net_flow_country
        )

    exchange_list = ExchangeList(logger)
    exchange_list.append(
        zoneKey=sorted_zone_keys,
        datetime=timestamp,
        netFlow=net_flows[sorted_zone_keys],
        source=EXCHANGE_SOURCE,
    )
    return exchange_list.to_list()


def fetch_consumption(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Fetches consumption of Panama."""

    if target_datetime is not None:
        raise ParserException(
            PARSER, "This parser is not yet able to parse historical data", zone_key
        )

    r = session or Session()
    timestamp = datetime.now(tz=TIMEZONE)
    response = r.get(CONSUMPTION_URL)
    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching production error code: {response.status_code}: {response.text}",
            zone_key,
        )

    response_payload = response.json()

    total_demand_payload = response_payload["data"][1]
    assert total_demand_payload["name"] == "Carga total"
    consumption_val = float(total_demand_payload["value"])

    consumption_list = TotalConsumptionList(logger)
    consumption_list.append(
        zoneKey=zone_key,
        datetime=timestamp,
        consumption=consumption_val,
        source=PRODUCTION_SOURCE,
    )
    return consumption_list.to_list()


if __name__ == "__main__":
    # main method, never used by the Electricity Map backend, but handy for testing

    print("fetch_production() ->")
    print(fetch_production())

    print("fetch_exchange() ->")
    print(fetch_exchange())
    # print("fetch_exchange(SV, PA) ->")
    # print(fetch_exchange(ZoneKey("SV"), ZoneKey("PA")))

    print("fetch_consumption() ->")
    print(fetch_consumption())
