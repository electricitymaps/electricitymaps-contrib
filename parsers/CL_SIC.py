#!/usr/bin/env python3

"""Parser for the SIC grid region of Chile."""

import arrow
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime
import pandas as pd
import re
import requests


thermal_plants = {
  "Taltal 2 GNL": "gas",
  "Taltal 2": "gas",
  "Taltal 2 Diesel": "oil",
  "Taltal 1 GNL": "gas",
  "Taltal 1": "gas",
  "Taltal 1 Diesel": "oil",
  "Diego de Almagro": "oil",
  "El Salvador": "oil",
  "Guacolda 1": "coal",
  "Guacolda 2": "coal",
  "Guacolda 3": "coal",
  "Guacolda 4": "coal",
  "Guacolda 5": "coal",
  "Huasco TG": "oil",
  "Huasco TG IFO": "oil",
  "L.Verde TG": "oil",
  "Los Vientos TG": "gas",
  "Nehuenco": "gas",
  "Nehuenco Diesel": "oil",
  "Nehuenco GNL": "gas",
  "Nehuenco TG 9B": "oil",
  "Nehuenco TG 9B Diesel": "oil",
  "Nehuenco TG 9B GNL": "gas",
  "Nehuenco II": "gas",
  "Nehuenco II Diesel": "oil",
  "Nehuenco II GNL": "gas",
  "San Isidro": "gas",
  "San Isidro Diesel": "oil",
  "San Isidro GNL": "gas",
  "San Isidro II": "gas",
  "San Isidro II Diesel": "oil",
  "San Isidro II GNL": "gas",
  "Ventanas 1": "coal",
  "Ventanas 2": "coal",
  "Nueva Ventanas": "coal",
  "L.Verde TV": "oil",
  "Nueva Renca GNL": "gas",
  "Nueva Renca FA_GLP": "gas",
  "Nueva Renca FA_GNL": "gas",
  "Nueva Renca Diesel": "oil",
  "Renca U1": "oil",
  "Renca U2": "oil",
  "Campiche": "coal",
  "Constitución A. Biomasa": "biomass",
  "Constitución A. IFO": "oil",
  "Petropower": "coal",
  "Laja": "biomass",
  "Bocamina": "coal",
  "Bocamina 2": "coal",
  "Arauco": "biomass",
  "Cholguán Biomasa": "biomass",
  "Cholguán IFO": "oil",
  "Licantén Biomasa": "biomass",
  "Licantén LN": "oil",
  "Valdivia LN": "oil",
  "Valdivia Biomasa": "biomass",
  "Valdivia IFO": "oil",
  "Antilhue TG": "oil",
  "Horcones TG": "oil",
  "Horcones Diesel": "oil",
  "TG_Coronel": "gas",
  "TG_Coronel Diesel": "oil",
  "Nueva Aldea": "biomass",
  "Nueva Aldea 2": "oil",
  "Nueva Aldea 3": "biomass",
  "Viñales": "biomass",
  "Candelaria 1": "gas",
  "Candelaria 1 Diesel": "oil",
  "Candelaria 1 GNL": "gas",
  "Candelaria 2": "gas",
  "Candelaria 2 Diesel": "oil",
  "Candelaria 2 GNL": "gas",
  "Trongol-Curanilahue": "oil",
  "Lebu": "oil",
  "Cañete": "oil",
  "Chufkén (Traiguén)": "oil",
  "Curacautín": "oil",
  "Yungay G1": "unknown",
  "Yungay G2": "unknown",
  "Yungay G3": "unknown",
  "Yungay Diesel 1": "oil",
  "Yungay Diesel 2": "oil",
  "Yungay Diesel 3": "oil",
  "Yungay 4ca": "oil",
  "Casablanca 1": "oil",
  "Casablanca 2": "oil",
  "Las Vegas": "oil",
  "Curauma": "oil",
  "Concón": "oil",
  "Escuadrón (ex FPC)": "biomass",
  "Constitución 1": "oil",
  "Maule": "oil",
  "Monte Patria": "oil",
  "Punitaqui": "oil",
  "Esperanza 1": "oil",
  "Esperanza 2": "oil",
  "Esperanza TG": "oil",
  "Degañ": "oil",
  "Olivos": "oil",
  "El Totoral": "oil",
  "Quintay": "oil",
  "Placilla": "oil",
  "Chiloé": "oil",
  "Quellon II": "oil",
  "Colmito GNL": "gas",
  "Colmito Diesel": "oil",
  "Los Pinos": "oil",
  "Chuyaca": "oil",
  "Skretting": "oil",
  "Cenizas": "oil",
  "Santa Lidia": "gas",
  "Trapén": "oil",
  "Los Espinos": "oil",
  "San Gregorio": "oil",
  "Linares Norte": "oil",
  "Biomar": "oil",
  "Eagon": "oil",
  "Salmofood I": "oil",
  "Teno": "oil",
  "Newen Diesel": "oil",
  "Newen Butano": "gas",
  "Newen Propano": "gas",
  "Newen Gas Natural": "gas",
  "Newen Mezcla Butano/Propano": "gas",
  "Watts I": "oil",
  "Watts II": "oil",
  "Multiexport I": "oil",
  "Multiexport II": "oil",
  "Los Álamos": "oil",
  "Cardones": "oil",
  "Quintero DIESEL A": "oil",
  "Quintero DIESEL B": "oil",
  "Quintero GNL A": "gas",
  "Quintero GNL B": "gas",
  "Louisiana Pacific": "oil",
  "El Peñón": "oil",
  "San Lorenzo de D. de Almagro U1": "gas",
  "San Lorenzo de D. de Almagro U2": "gas",
  "San Lorenzo de D. de Almagro U3": "gas",
  "Tapihue": "gas",
  "Termopacífico": "oil",
  "Loma Los Colorados I": "biomass",
  "Loma Los Colorados II": "biomass",
  "Emelda U1": "oil",
  "Emelda U2": "oil",
  "Colihues IFO": "oil",
  "Colihues DIE": "oil",
  "Curicó": "unknown",
  "Punta Colorada IFO": "oil",
  "Punta Colorada Diesel": "oil",
  "Masisa (Cabrero)": "biomass",
  "Calle-Calle": "oil",
  "Cem Bio Bio IFO": "oil",
  "Cem Bio Bio DIESEL": "oil",
  "Southern": "oil",
  "Lousiana Pacific II (Lautaro)": "oil",
  "HBS": "biomass",
  "Tomaval": "unknown",
  "Skretting Osorno": "oil",
  "Energía Pacífico": "oil",
  "Lonquimay": "oil",
  "Tirúa": "oil",
  "Lautaro-Comasa": "biomass",
  "Lautaro-Comasa 2": "biomass",
  "Danisco": "oil",
  "Contulmo": "oil",
  "JCE": "oil",
  "Santa María": "coal",
  "Estancilla": "oil",
  "Trebal Mapocho": "biomass",
  "CMPC Laja": "biomass",
  "Tamm": "biomass",
  "Ancalí 1": "biomass",
  "Santa Fe": "biomass",
  "Santa Marta": "biomass",
  "Santa Irene": "biomass",
  "Las Pampas": "biomass",
  "CMPC Pacífico": "biomass",
  "Energía León (Coelemu)": "biomass",
  "CMPC Santa Fe": "biomass",
  "Biocruz": "gas",
  "Los Guindos": "oil",
  "CMPC Cordillera": "gas",
  "CMPC Tissue": "gas",
  "Andes Generación 1 Diesel": "oil",
  "Andes Generación 2 Diesel": "oil",
  "Andes Generación 3 Diesel": "oil",
  "Andes Generación 4 Diesel": "oil",
  "Andes Generación 1 FO6": "oil",
  "Andes Generación 2 FO6": "oil",
  "Andes Generación 3 FO6": "oil",
  "Andes Generación 4 FO6": "oil",
  "El Molle": "biomass",
  "El Canelo 1": "oil",
  "Raso Power": "unknown",
  "HBS GNL": "gas",
  "Rey": "oil",
  "El Nogal": "oil",
  "Lepanto": "biomass"
}


def get_xls_data(session = None):
    """Finds and reads .xls file from url into a pandas dataframe."""

    s = session or requests.Session()
    document_url = 'https://sic.coordinador.cl/informes-y-documentos/fichas/operacion-real/'
    req = s.get(document_url)
    soup = BeautifulSoup(req.text, 'html.parser')

    # Find the latest file.
    generation_link = soup.find("a", {"title": "Descargar archivo"})
    extension = generation_link["href"]
    base_url = "https://sic.coordinador.cl"
    data_url = base_url + extension

    date_pattern = r'OP(\d+)\.xls'
    date_str = re.search(date_pattern, extension).group(1)

    date_no_tz = arrow.get(date_str, "YYMMDD")
    date = date_no_tz.replace(tzinfo='Chile/Continental')

    col_names = ['Plants'] + list(range(1,24)) + [0]
    df = pd.read_excel(data_url, skiprows=[0,1,2,3], header=None, index_col=0, skip_footer=300, usecols=25, names=col_names)
    df = df.reset_index(drop=True)
    df = df.set_index("Plants")

    return df, date


def combine_generating_units(generation, gen_vals):
    """Takes a list of dictionaries with identical keys and combines them using a defaultdict."""

    for unit in generation:
        for k, v in unit.items():
            gen_vals[k] += v

    return dict(gen_vals)


def thermal_processer(df, logger):
    """
    Creates a separate dataframe containing only thermal plants.
    Each row is a plant with each column being an hour's generation.
    Returns a tuple containing 5 dictionaries of generation types.
    """

    thermal_start = df.index.get_loc('Térmicas')
    thermal_end = df.index.get_loc('Embalse')

    thermal_df = df.iloc[thermal_start+1:thermal_end]

    # Log any new plants that have been added.
    data_plants = list(thermal_df.index)
    map_plants = list(thermal_plants.keys())
    unmapped = list(set(data_plants) - set(map_plants))

    for plant in unmapped:
        logger.warning("{} is missing from the CL-SIC thermal plant mapping.".format(plant))

    coal_generation = []
    gas_generation = []
    oil_generation = []
    biomass_generation = []
    unknown_generation = []

    for plant in thermal_plants.keys():
        plant_vals = thermal_df.loc[plant].to_dict()
        plant_type = thermal_plants[plant]
        if plant_type == 'coal':
            coal_generation.append(plant_vals)
        elif plant_type == 'gas':
            gas_generation.append(plant_vals)
        elif plant_type == 'oil':
            oil_generation.append(plant_vals)
        elif plant_type == 'biomass':
            biomass_generation.append(plant_vals)
        else:
            unknown_generation.append(plant_vals)

    coal_vals = defaultdict(lambda: 0.0)
    gas_vals = defaultdict(lambda: 0.0)
    oil_vals = defaultdict(lambda: 0.0)
    biomass_vals = defaultdict(lambda: 0.0)
    unknown_vals = defaultdict(lambda: 0.0)

    coal = combine_generating_units(coal_generation, coal_vals)
    gas = combine_generating_units(gas_generation, gas_vals)
    oil = combine_generating_units(oil_generation, oil_vals)
    biomass = combine_generating_units(biomass_generation, biomass_vals)
    unknown = combine_generating_units(unknown_generation, unknown_vals)

    return coal, gas, oil, biomass, unknown


def data_processer(df, date, logger):
    """
    Extracts aggregated data for hydro, solar and wind from dataframe.
    Combines with thermal data and an arrow object timestamp.
    Returns a list of 2 element tuples.
    """

    thermal_generation = thermal_processer(df, logger)
    coal_vals = thermal_generation[0]
    gas_vals = thermal_generation[1]
    oil_vals = thermal_generation[2]
    biomass_vals = thermal_generation[3]
    unknown_vals = thermal_generation[4]

    total = df.loc['Total Generación SIC']

    hydro = df.loc['Hidroeléctrico'].to_dict()
    solar = df.loc['Solar'].to_dict()
    wind = df.loc['Eólico'].to_dict()

    hydro_vals = {k: hydro[k]*total[k] for k in hydro}
    solar_vals = {k: solar[k]*total[k] for k in solar}
    wind_vals = {k: wind[k]*total[k] for k in wind}

    generation_by_hour = []
    for hour in range(0,24):
        production = {}
        production['hydro'] = hydro_vals[hour]
        production['wind'] = wind_vals[hour]
        production['solar'] = solar_vals[hour]
        production['coal'] = coal_vals[hour]
        production['gas'] = gas_vals[hour]
        production['oil'] = oil_vals[hour]
        production['biomass'] = biomass_vals[hour]
        production['unknown'] = unknown_vals[hour]

        if hour == 0:
            # Midnight data is for a new day.
            dt = date.shift(days=+1)
        else:
            dt = date.replace(hour=hour)

        generation_by_hour.append((dt, production))

    return generation_by_hour


def fetch_production(zone_key = 'CL-SIC', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country
    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional) -- request session passed in order to re-use an existing session
    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'datetime': '2017-01-01T00:00:00Z',
      'production': {
          'biomass': 0.0,
          'coal': 0.0,
          'gas': 0.0,
          'hydro': 0.0,
          'nuclear': null,
          'oil': 0.0,
          'solar': 0.0,
          'wind': 0.0,
          'geothermal': 0.0,
          'unknown': 0.0
      },
      'storage': {
          'hydro': -10.0,
      },
      'source': 'mysource.com'
    }
    """

    gxd = get_xls_data(session = None)
    processing = data_processer(gxd[0], gxd[1], logger)

    data_by_hour = []
    for processed_data in processing:
        dt = processed_data[0].datetime
        production = processed_data[1]

        datapoint = {
          'zoneKey': zone_key,
          'datetime': dt,
          'production': production,
          'storage': {},
          'source': 'sic.coordinador.cl'
        }

        data_by_hour.append(datapoint)

    return data_by_hour


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
