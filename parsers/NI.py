#!/usr/bin/env python3
# coding=utf-8

from collections import defaultdict
from logging import getLogger

import arrow
import requests

from .lib.validation import validate

TIMEZONE = "America/Managua"

MAP_URL = "http://www.cndc.org.ni/graficos/MapaSIN/index.php"
SUMMARY_URL = "http://www.cndc.org.ni/graficos/graficaGeneracion_Tipo_TReal0000.php"
PRICE_URL = (
    "http://www.cndc.org.ni/consultas/infoRelevanteSIN/consultaCostoMarginal.php"
)

# This is a list in same order as values for "generacion" variable in MAP_URL
# as of 2017-07-08.
# It was obtained by matching each generation value to the graphic and name on the map,
# by changing the formatter function in JS source to print the index along with the value.
# Per the following sources:
# - https://global-climatescope.org/markets/ni, "Installed capacity" section,
# - https://www.cndc.org.ni/Publicaciones/InformeDiarioSIN/Informe_Ejecutivo.pdf,
# - Wikipedia: https://en.wikipedia.org/wiki/Electricity_sector_in_Nicaragua#Installed_capacity (quoting a 2006 report),
# all of "thermal" / fossil fuel generation is using oil/diesel.
# Geothermal and biomass classification of Momotombo, San Jacinto, and Monte Rosa
# is also per https://en.wikipedia.org/wiki/Electricity_sector_in_Nicaragua
PLANT_CLASSIFICATIONS = [
    "hydro",  # Centroamerica
    "thermal",  # PCG VI
    "thermal",  # Acahualinca / PLB
    "geothermal",  # Momotombo - geothermal per Wikipedia
    "biomass",  # Monte Rosa - biomass per Wikipedia
    "thermal",  # Planta Nicaragua
    "thermal",  # PCG VII
    "thermal",  # Managua
    "thermal",  # Planta Corinto
    "thermal",  # Tipitapa
    "thermal",  # Censa-Amfels
    "thermal",  # Acahualinca / PHC I
    "thermal",  # Los Brasilies / PHC II
    "thermal",  # Canal
    "thermal",  # PCG II
    "thermal",  # Managua/PCG III
    "thermal",  # PCG IV
    "thermal",  # PCG V
    "thermal",  # PCG I
    "thermal",  # PCG VIII
    "wind",  # Amayo
    "geothermal",  # San Jacinto - geothermal per Wikipedia
    "wind",  # Blue Power
    "wind",  # Eolo
    "wind",  # Alba Rivas
    "hydro",  # Hidropantasma
    "hydro",  # Larreynaga
    "thermal",  # Montelimar
    "thermal",  # Planta Man
    "hydro",  # C. Fonseca
]


# REFERENCE_TOTAL_PRODUCTION = 433  # MW


def extract_text(full_text, start_text, end_text=None):
    start = full_text.find(start_text)

    if start == -1:
        return full_text

    start += len(start_text)

    if not end_text:
        return full_text[start:]

    end = full_text.find(end_text, start)

    if end == -1:
        return full_text[start:]
    else:
        return full_text[start:end]


def get_time_from_system_map(text):
    # date format is: "'Actualizado: 07/07/2017 01:00:50 PM'"

    datetime_text = extract_text(text, "Actualizado: ", "'")
    datetime_arrow = arrow.get(datetime_text, "DD/MM/YYYY hh:mm:ss A")
    datetime_datetime = arrow.get(datetime_arrow.datetime, TIMEZONE).datetime

    return datetime_datetime


def get_production_from_map(requests_obj) -> tuple:
    """
    Get frequently-updated information on MAP_URL.
    This page is programmed to refresh every 10 seconds, and the timestamp
    in its text indicates that the information is updated every 10 to 30 seconds.

    However, it seems to bundle in solar generation with generation at another plant.
    get_production_from_summary() includes solar explictly.

    :return: tuple(production, datetime_datetime).
    """

    response = requests_obj.get(MAP_URL)
    response.encoding = "utf-8"
    map_html = response.text

    data_datetime = get_time_from_system_map(map_html)

    generation_text = extract_text(map_html, "var generacion", "];")
    generation_text = extract_text(generation_text, "[")
    generation_list = [
        float(g.replace("'", "") or 0) for g in generation_text.split(",")
    ]

    production = {key: 0 for key in set(PLANT_CLASSIFICATIONS)}

    for index, val in enumerate(generation_list[: len(PLANT_CLASSIFICATIONS)]):
        plant_type = PLANT_CLASSIFICATIONS[index]
        production[plant_type] += val

    # Thermal is oil - see comment at PLANT_CLASSIFICATIONS
    production["oil"] = production.pop("thermal")

    return production, data_datetime


def get_production_from_summary(requests_obj) -> tuple:
    """
    Get information from SUMMARY_URL.
    This is updated once an hour, on the hour.

    Units are the same as in MAP_URL.
    Values match the values reported in MAP_URL on the hour very closely, within 1-3%.

    However, unlike get_production_from_map(), this includes solar generation,
    which, although small, is nice to specify.

    :return: tuple(production, datetime_datetime).
    """

    type_translator = {
        "EOLICO": "wind",
        "GEOTERMICO": "geothermal",
        "BIOMASA": "biomass",
        "HIDROELECTRICO": "hydro",
        "SOLAR": "solar",
        # all "thermal" / fossil fuel is oil - see comment at PLANT_CLASSIFICATIONS
        "TERMICO BUNKER": "oil",
        "TERMICO DIESEL": "oil",
    }

    response = requests_obj.get(SUMMARY_URL)
    response.encoding = "utf-8"
    gentype_html = response.text

    datetime_text = extract_text(gentype_html, "Consultado a las ", "'")
    hour = extract_text(datetime_text, "", " horas")
    d = extract_text(datetime_text, "del dia ")
    datetime_arrow = arrow.get(d + " " + hour, "DD/MM/YYYY HH")
    datetime_datetime = arrow.get(datetime_arrow.datetime, TIMEZONE).datetime

    gen_type_text = extract_text(gentype_html, "Tipo de Generación", "center:")
    gen_type_text = extract_text(gen_type_text, "[")

    production = defaultdict(list)

    # One of the generation types is featured by default in the pie chart.
    # This makes its HTML/JS specification be different.
    # The type which is featured also differs from hour to hour.
    featured_type = extract_text(gen_type_text, "{", "}")
    featured_type_props = featured_type.split(",")
    featured_type_dict = {
        x.split(":")[0].strip(): x.split(":")[1].strip() for x in featured_type_props
    }
    featured_type_name = featured_type_dict["name"].replace("'", "")
    featured_type_val = float(featured_type_dict["y"])

    featured_type_standard_name = type_translator.get(featured_type_name, "unknown")
    production[featured_type_standard_name].append(featured_type_val)

    # The remaining, non-featured generation types are all formatted the same.
    other_types = extract_text(gen_type_text, "}")
    other_types_props = [t.split(",") for t in other_types.split("[")]
    for other_type in other_types_props:
        name = other_type[0]
        val = other_type[1]
        if name:
            standard_name = type_translator.get(name.replace("'", ""), "unknown")
            production[standard_name].append(float(val.replace("]", "").strip()))

    production = {k: sum(v) for k, v in production.items()}

    return production, datetime_datetime


def fetch_production(
    zone_key="NI", session=None, target_datetime=None, logger=getLogger(__name__)
) -> dict:
    """Requests the last known production mix (in MW) of Nicaragua."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()

    # We're currently using the summary page (SUMMARY_URL, via get_production_from_summary())
    # rather than the detailed map page (MAP_URL, via get_production_from_map())
    # in order to get solar production.
    production, data_datetime = get_production_from_summary(requests_obj)

    # Explicitly report types that are not used in Nicaragua as zero.
    # Source for the installed capacity of Nicaragua is INE (Nicaraguan Institute of Energy -- see link in DATA_SOURCES.md).
    production.update({"nuclear": 0, "coal": 0, "gas": 0})

    data = {
        "datetime": data_datetime,
        "zoneKey": zone_key,
        "production": production,
        "storage": {},
        "source": "cndc.org.ni",
    }

    return validate(data, logger, expected_range=(86.6, 2165))


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=getLogger(__name__)
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    requests_obj = session or requests.session()

    response = requests_obj.get(MAP_URL)
    map_html = response.text

    # In the list of interconnections in the HTML source of MAP_URL,
    # the first two are with Honduras, and the second two with Costa Rica.

    # Cross-comparing regional data on http://www.enteoperador.org/newsite/flash/SER.html
    # and NI data on MAP_URL (both fairly real-time), we can see that
    # on the NI MAP_URL page, negative is import to NI, and positive is export from NI.

    # Because in both possible sorted_zone_key values (HN->NI and CR->NI) NI is second,
    # we expect netFlow to be positive when NI is importing, and negative when NI is exporting.
    # So multiply value reported by the MAP_URL by -1.

    interchange_text = extract_text(map_html, "var interconexion", "];")
    interchange_text = extract_text(interchange_text, "[")
    interchange_list = [
        float(g.replace("'", "") or 0) for g in interchange_text.split(",")
    ]

    if sorted_zone_keys == "HN->NI":
        flow = -1 * (interchange_list[0] + interchange_list[1])
    elif sorted_zone_keys == "CR->NI":
        flow = -1 * (interchange_list[2] + interchange_list[3])
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    data = {
        "datetime": get_time_from_system_map(map_html),
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": flow,
        "source": "cndc.org.ni",
    }

    return data


def fetch_price(
    zone_key="NI", session=None, target_datetime=None, logger=getLogger(__name__)
) -> list:
    """Requests the most recent known power prices in Nicaragua grid."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()
    response = requests_obj.get(PRICE_URL)
    response.encoding = "utf-8"
    prices_html = response.text

    now_local_time = arrow.utcnow().to(TIMEZONE)
    midnight_local_time = (
        arrow.utcnow().to(TIMEZONE).replace(hour=0, minute=0, second=0, microsecond=0)
    )

    hours_text = prices_html.split("<br />")

    data = []
    for hour_data in hours_text:
        if not hour_data:
            # there is usually an empty item at the end of the list, ignore it
            continue

        # hour_data is like "Hora 13:&nbsp;&nbsp;   84.72"
        hour = int(extract_text(hour_data, "Hora ", ":"))
        price = float(extract_text(hour_data, "&nbsp;   ").replace(",", "."))

        price_date = midnight_local_time.replace(hour=hour)
        if price_date > now_local_time:
            # data for previous day is also included
            price_date = price_date.replace(days=-1)

        data.append(
            {
                "zoneKey": zone_key,
                "datetime": price_date.datetime,
                "currency": "USD",
                "price": price,
                "source": "cndc.org.ni",
            }
        )

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print('fetch_exchange("NI", "HN") ->')
    print(fetch_exchange("NI", "HN"))
    print('fetch_exchange("NI", "CR") ->')
    print(fetch_exchange("NI", "CR"))

    print('fetch_price("NI") ->')
    print(fetch_price("NI"))
