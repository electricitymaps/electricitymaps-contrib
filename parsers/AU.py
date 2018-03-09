#!/usr/bin/env python3

import json

# The arrow library is used to handle datetimes
import arrow
import numpy as np
import pandas as pd
# The request library is used to fetch content through HTTP
import requests

from .lib import AU_battery, AU_solar

AMEO_CATEGORY_DICTIONARY = {
    'Bagasse': 'biomass',
    'Black Coal': 'coal',
    'Brown Coal': 'coal',
    'coal': 'coal',
    'Coal Seam Methane': 'gas',
    'Diesel': 'oil',
    'gas': 'gas',
    'hydro': 'hydro',
    'Hydro': 'hydro',
    'Kerosene': 'oil',
    'Landfill / Biogas': 'biomass',
    'Landfill / Biogass': 'biomass',
    'Landfill Gas': 'biomass',
    'Landfill Methane / Landfill Gas': 'biomass',
    'Landfill, Biogas': 'biomass',
    'Macadamia Nut Shells': 'biomass',
    'Natural Gas': 'gas',
    'Natural Gas / Diesel': 'gas',
    'Natural Gas / Fuel Oil': 'gas',
    'oil': 'oil',
    'Sewerage/Waste Water': 'biomass',
    'Solar': 'solar',
    'Solar PV': 'solar',
    'Waste Coal Mine Gas': 'gas',
    'Waste Water / Sewerage': 'biomass',
    'Water': 'hydro',
    'Wind': 'wind'
}

AMEO_LOCATION_DICTIONARY = {
    'Hallett Power Station': 'AUS-SA',
    'Somerton Power Station': 'AUS-VIC',
    'AGL SITA Landfill1 Kemps Creek': 'AUS-NSW',
    'Angaston Power Station': 'AUS-SA',
    'Ararat Wind Farm': 'AUS-VIC',
    'Awaba Power Station': 'AUS-NSW',
    'Bald Hills Wind Farm': 'AUS-VIC',
    'Bankstown Sports Club Plant Units': 'AUS-NSW',
    'Banimboola Power Station': 'AUS-VIC',
    'Barcaldine Power Station': 'AUS-QLD',
    'Barcaldine Solar Farm': 'AUS-QLD',
    'Barron Gorge Power Station': 'AUS-QLD',
    'Basslink HVDC Link': None,
    'Bastyan Power Station': 'AUS-TAS',
    'Ballarat Base Hospital Plant': 'AUS-VIC',
    'Bell Bay Three Power Station': 'AUS-TAS',
    'Bairnsdale Power Station': 'AUS-VIC',
    'Burrendong Hydro Power Station': 'AUS-NSW',
    'Blowering Power Station': 'AUS-NSW',
    'The Bluff Wind Farm': 'AUS-SA',
    'Blue Lake Milling Power Plant': 'AUS-SA',
    'Boco Rock Wind Farm': 'AUS-NSW',
    'SA Water Bolivar Waste Water Treatment (WWT) Plant': 'AUS-SA',
    'Browns Plains Land Fill Gas Power Station': 'AUS-QLD',
    'Braemar Power Station': 'AUS-QLD',
    'Braemar 2 Power Station': 'AUS-QLD',
    'Broadmeadows Landfill Gas Power Station': 'AUS-VIC',
    'Broken Hill Solar Plant': 'AUS-NSW',
    'Brooklyn Landfill Gas Power Station': 'AUS-VIC',
    'Brown Mountain': 'AUS-NSW',
    'Burrinjuck Power Station': 'AUS-NSW',
    'Butlers Gorge Power Station': 'AUS-TAS',
    'Bayswater Power Station': 'AUS-NSW',
    'Broadwater Power Station Units 1 and 2': 'AUS-NSW',
    'Callide A Power Station': 'AUS-QLD',
    'Callide B Power Station': 'AUS-QLD',
    'Capital Wind Farm': 'AUS-NSW',
    'Catagunya Diesel Generation ': 'AUS-TAS',
    'Cathedral Rocks Wind Farm': 'AUS-SA',
    'Coonooer Bridge Wind Farm': 'AUS-VIC',
    'Capital East Solar Farm': 'AUS-NSW',
    'Cethana Power Station': 'AUS-TAS',
    'Colongra Power Station': 'AUS-NSW',
    'Challicum Hills Wind Farm': 'AUS-VIC',
    'Claytons Landfill Gas Power Station': 'AUS-VIC',
    'Clements Gap Wind Farm': 'AUS-SA',
    'Cluny Power Station': 'AUS-TAS',
    'Codrington Wind Farm': 'AUS-VIC',
    'Condong Power Station Unit 1': 'AUS-NSW',
    'Copeton Hydro Power Station': 'AUS-NSW',
    'Corio Landfill Gas Power Station': 'AUS-VIC',
    'Callide Power Plant': 'AUS-QLD',
    'Condamine Power Station A': 'AUS-QLD',
    'Cullerin Range Wind Farm': 'AUS-NSW',
    'Daandine Power Station': 'AUS-QLD',
    'Dartmouth Power Station': 'AUS-VIC',
    'Darling Downs Power Station': 'AUS-QLD',
    'Devils Gate Power Station': 'AUS-TAS',
    'Dry Creek Gas Turbine Station': 'AUS-SA',
    'Eastern Creek Power Station': 'AUS-NSW',
    'Eildon Pondage Hydro Power Station': 'AUS-VIC',
    'Eildon Power Station': 'AUS-VIC',
    'Eraring Power Station': 'AUS-NSW',
    'Fisher Power Station': 'AUS-TAS',
    'Broken Hill Gas Turbines': 'AUS-NSW',
    'George Town Diesel Generation': 'AUS-TAS',
    'German Creek Power Station': 'AUS-QLD',
    'Glenbawn Hydro Power Station': 'AUS-NSW',
    'Glenmaggie Hydro Power Station': 'AUS-VIC',
    'Gordon Power Station': 'AUS-TAS',
    'Grange Avenue Power Station, Grange Avenue Landfill Gas Power Station': 'AUS-NSW',
    'Gladstone Power Station': 'AUS-QLD',
    'Gullen Range Wind Farm': 'AUS-NSW',
    'Gunning Wind Farm': 'AUS-NSW',
    'Guthega Power Station': 'AUS-NSW',
    'Hallam Road Renewable Energy Facility': 'AUS-VIC',
    'Hallett 1 Wind Farm': 'AUS-SA',
    'Hallett 2 Wind Farm': 'AUS-SA',
    'Hepburn Wind Farm': 'AUS-VIC',
    'Hornsdale Wind Farm': 'AUS-SA',
    'Hornsdale Wind Farm 2': 'AUS-SA',
    'Hunter Economic Zone': 'AUS-NSW',
    'Highbury Landfill Gas Power Station Unit 1': 'AUS-SA',
    'Hume Power Station': 'AUS-NSW',
    'Hunter Valley Gas Turbine': 'AUS-NSW',
    'Hazelwood Power Station': None,  # Closed
    'ISIS Central Sugar Mill Co-generation Plant': 'AUS-QLD',
    'Invicta Sugar Mill': 'AUS-QLD',
    'Jacks Gully Landfill Gas Power Station': 'AUS-NSW',
    'John Butters Power Station': 'AUS-TAS',
    'Jeeralang "A" Power Station': 'AUS-VIC',
    'Jeeralang "B" Power Station': 'AUS-VIC',
    'Jindabyne Small Hydro Power Station': 'AUS-NSW',
    'Jounama Small Hydro Power Station': 'AUS-NSW',
    'Kareeya Power Station': 'AUS-QLD',
    'Keepit Power Station': 'AUS-NSW',
    'Kincumber Landfill Site': 'AUS-NSW',
    'Kogan Creek Power Station': 'AUS-QLD',
    'Ladbroke Grove Power Station': 'AUS-SA',
    'Liddell Power Station': 'AUS-NSW',
    'Lemonthyme / Wilmot  Power Station': 'AUS-TAS',
    'Catagunya / Liapootah / Wayatinah Power Station': 'AUS-TAS',
    'Lake Bonney Wind Farm': 'AUS-SA',
    'Lake Bonney Stage 2 Windfarm': 'AUS-SA',
    'Lake Bonney Stage 3 Wind Farm': 'AUS-SA',
    'Lake Echo Power Station': 'AUS-TAS',
    'Laverton North Power Station': 'AUS-VIC',
    'Longford Plant': 'AUS-VIC',
    'Lonsdale Power Station': 'AUS-SA',
    'Loy Yang B Power Station': 'AUS-VIC',
    'Lucas Heights 2 LFG Power Station': 'AUS-NSW',
    'Loy Yang A Power Station': 'AUS-VIC',
    'Macarthur Wind Farm': 'AUS-VIC',
    'Mackay Gas Turbine': 'AUS-QLD',
    'Mackintosh Power Station': 'AUS-TAS',
    'Moranbah North Power Station, Grosvenor 1 Waste Coal Mine Gas Power Station': 'AUS-QLD',
    'Bogong / Mckay Power Station': 'AUS-VIC',
    'Meadowbank Diesel Generation': 'AUS-TAS',
    'Meadowbank Power Station': 'AUS-TAS',
    'Mt Mercer Wind Farm': 'AUS-VIC',
    'Midlands Power Station': 'AUS-TAS',
    'Mintaro Gas Turbine Station': 'AUS-SA',
    'Mortons Lane Wind Farm': 'AUS-VIC',
    'Moranbah Generation Project': 'AUS-QLD',
    'Moree Solar Farm': 'AUS-NSW',
    'Mornington Waste Disposal Facility': 'AUS-VIC',
    'Mortlake Power Station Units': 'AUS-VIC',
    'Mt Piper Power Station': 'AUS-NSW',
    'Millmerran Power Plant': 'AUS-QLD',
    'Mt Stuart Power Station': 'AUS-QLD',
    'Mt Millar Wind Farm': 'AUS-SA',
    'Mugga Lane Solar Park': 'AUS-NSW',
    'Murray 1 Power Station, Murray 2 Power Station': 'AUS-NSW',
    'Musselroe Wind Farm': 'AUS-TAS',
    'North Brown Hill Wind Farm': 'AUS-SA',
    'Nine Network Willoughby Plant': 'AUS-NSW',
    'Newport Power Station': 'AUS-VIC',
    'Northern Power Station': None,  # Closed
    'Nyngan Solar Plant': 'AUS-NSW',
    'Oakey Power Station': 'AUS-QLD',
    'Oaklands Hill Wind Farm': 'AUS-VIC',
    'Oaky Creek 2 Waste Coal Mine Gas Power Station Units 1-15': 'AUS-QLD',
    'Oaky Creek  Power Station': 'AUS-QLD',
    'Osborne Power Station': 'AUS-SA',
    'Paloona Power Station': 'AUS-TAS',
    'Pedler Creek Landfill Gas Power Station Units 1-3': 'AUS-SA',
    'Pindari Hydro Power Station': 'AUS-NSW',
    'Playford B Power Station': None,  # Closed
    'Poatina Power Station': 'AUS-TAS',
    'Port Lincoln Gas Turbine': 'AUS-SA',
    'Port Latta Diesel Generation': 'AUS-TAS',
    'Portland Wind Farm': 'AUS-VIC',
    'Pelican Point Power Station': 'AUS-SA',
    'Port Stanvac Power Station 1': 'AUS-SA',
    'Wivenhoe Power Station No. 1 Pump': 'AUS-QLD',
    'Wivenhoe Power Station No. 2 Pump': 'AUS-QLD',
    'Quarantine Power Station': 'AUS-SA',
    'Reece Power Station': 'AUS-TAS',
    'Remount Power Station': 'AUS-TAS',
    'Repulse Power Station': 'AUS-TAS',
    'Rochedale Renewable Energy Facility': 'AUS-QLD',
    'Roghan Road LFG Power Plant': 'AUS-QLD',
    'Roma Gas Turbine Station': 'AUS-QLD',
    'Rowallan Power Station': 'AUS-TAS',
    'Royalla Solar Farm': 'AUS-NSW',
    'Rocky Point Cogeneration Plant': 'AUS-QLD',
    'Shepparton Wastewater Treatment Facility': 'AUS-VIC',
    'Bendeela / Kangaroo Valley Power Station': 'AUS-NSW',
    'Bendeela / Kangaroo Valley Pumps': 'AUS-NSW',
    'Smithfield Energy Facility': 'AUS-NSW',
    'South East Water - Hallam Hydro Plant': 'AUS-VIC',
    'Snowtown Wind Farm Stage 2 North': 'AUS-SA',
    'Snowtown South Wind Farm': 'AUS-SA',
    'Snowtown Wind Farm Units 1 to 47': 'AUS-SA',
    'Snuggery Power Station': 'AUS-SA',
    'Stanwell Power Station': 'AUS-QLD',
    'Starfish Hill Wind Farm': 'AUS-SA',
    'St George Leagues Club Plant': 'AUS-NSW',
    'Southbank Institute Of Technology Unit 1 Plant': 'AUS-QLD',
    'Suncoast Gold Macadamias': 'AUS-QLD',
    'Springvale Landfill Gas Power Station': 'AUS-NSW',
    'Swanbank E Gas Turbine': 'AUS-QLD',
    'Tallawarra Power Station': 'AUS-NSW',
    'Taralga Wind Farm': 'AUS-NSW',
    'Tarong Power Station': 'AUS-QLD',
    'Tarraleah Power Station': 'AUS-TAS',
    'Tatiara Bordertown Plant': 'AUS-SA',
    'Tatura Biomass Generator': 'AUS-VIC',
    'Tea Tree Gully Landfill Gas Power Station Unit 1': 'AUS-SA',
    'Teralba Power Station': 'AUS-NSW',
    'Terminal Storage Mini Hydro Power Station': 'AUS-SA',
    'Taralgon Network Support Station': 'AUS-VIC',
    'The Drop Hydro Unit 1': 'AUS-NSW',
    'Veolia Ti Tree Bio Reactor': 'AUS-QLD',
    'Tarong North Power Station': 'AUS-QLD',
    'Toora Wind Farm': 'AUS-VIC',
    'Torrens Island Power Station "A"': 'AUS-SA',
    'Torrens Island Power Station "B"': 'AUS-SA',
    'Trevallyn Power Station': 'AUS-TAS',
    'Tribute Power Station': 'AUS-TAS',
    'Tumut 3 Power Station': 'AUS-NSW',
    'Tungatinah Power Station': 'AUS-TAS',
    'Tamar Valley Combined Cycle Power Station': 'AUS-TAS',
    'Tamar Valley Peaking  Power Station': 'AUS-TAS',
    'Tumut 1 Power Station, Tumut 2 Power Station': 'AUS-NSW',
    'Uranquinty Power Station': 'AUS-NSW',
    'Vales Point "B" Power Station': 'AUS-NSW',
    'Valley Power Peaking Facility': 'AUS-VIC',
    'Wivenhoe Power Station': 'AUS-NSW',
    'Waterloo Wind Farm': 'AUS-SA',
    'Waubra Wind Farm': 'AUS-VIC',
    'Woodlawn Bioreactor Energy Generation Station': 'AUS-NSW',
    'Western Suburbs League Club (Campbelltown) Plant': 'AUS-NSW',
    'West Illawarra Leagues Club Plant': 'AUS-NSW',
    'Windy Hill Wind Farm': 'AUS-QLD',
    'Whitwood Road Renewable Energy Facility': 'AUS-QLD',
    'Wilga Park A Power Station': 'AUS-VIC',
    'Wilga Park B Power Station': 'AUS-VIC',
    'William Hovell Hydro Power Station': 'AUS-VIC',
    'Wingfield 1 Landfill Gas Power Station Units 1-4': 'AUS-SA',
    'Wingfield 2 Landfill Gas Power Station Units 1-4': 'AUS-SA',
    'West Kiewa Power Station': 'AUS-VIC',
    'West Nowra Landfill Gas Power Generation Facility': 'AUS-NSW',
    'Wollert Renewable Energy Facility': 'AUS-SA',
    'Wonthaggi Wind Farm': 'AUS-VIC',
    'Woodlawn Wind Farm': 'AUS-NSW',
    'Woolnorth Studland Bay / Bluff Point Wind Farm': 'AUS-TAS',
    'Woy Woy Landfill Site': 'AUS-NSW',
    'Wattle Point Wind Farm': 'AUS-VIC',
    'Wyangala A Power Station': 'AUS-NSW',
    'Wyangala B Power Station': 'AUS-NSW',
    'Wyndham Waste Disposal Facility': 'AUS-VIC',
    'Townsville Gas Turbine': 'AUS-QLD',
    'Yambuk Wind Farm': 'AUS-VIC',
    'Yarwun Power Station': 'AUS-QLD',
    'Yallourn W Power Station': 'AUS-VIC',
}

AMEO_STATION_DICTIONARY = {
    'Basslink HVDC Link': 'Import / Export',
    # 'Bendeela / Kangaroo Valley Pumps': 'storage',
    # 'Rocky Point Cogeneration Plant': 'storage',
    # 'Wivenhoe Power Station No. 1 Pump': 'storage',
    # 'Wivenhoe Power Station No. 2 Pump': 'storage',
    'Yarwun Power Station': 'coal'
}


def fetch_production(zone_key=None, session=None, target_datetime=None, logger=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

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
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    url = 'http://services.aremi.nationalmap.gov.au/aemo/v3/csv/all'
    df = pd.read_csv(url)
    data = {
        'zoneKey': zone_key,
        'capacity': {
            'coal': 0,
            'geothermal': 0,
            'hydro': 0,
            'nuclear': 0,
        },
        'production': {
            'coal': 0,
            'geothermal': 0,
            'hydro': 0,
            'nuclear': 0
        },
        'storage': {},
        'source': 'aremi.nationalmap.gov.au, pv-map.apvi.org.au',
    }

    # It's possible that the csv sometimes contains several timestamps.
    # https://github.com/tmrowco/electricitymap/issues/704
    # Find the latest timestamp.
    timestamps = df['Most Recent Output Time (AEST)'].dropna().values
    latest_ts = max([arrow.get(x) for x in timestamps.tolist()])
    data['datetime'] = latest_ts.datetime

    for rowIndex, row in df.iterrows():
        station = row['Station Name']
        fuelsource = row['Fuel Source - Descriptor']

        if station not in AMEO_LOCATION_DICTIONARY:
            logger.warning('WARNING: station %s does not belong to any state' % station)
            continue

        if AMEO_LOCATION_DICTIONARY[station] != zone_key:
            continue

        if row['Most Recent Output Time (AEST)'] == '-':
            continue

        key = (AMEO_CATEGORY_DICTIONARY.get(fuelsource, None) or
               AMEO_STATION_DICTIONARY.get(station, None))

        value = row['Current Output (MW)']
        if np.isnan(value):
            value = 0.0
        else:
            try:
                value = float(row['Current Output (MW)'])
            except ValueError:
                value = 0.0

        if not key:
            # Unrecognized source, ignore
            if value:
                # If it had production, show warning
                logger.warning('WARNING: key {} is not supported, row {}'.format(fuelsource, row))
            continue

        # Skip HVDC links
        if AMEO_CATEGORY_DICTIONARY.get(station, None) == 'Import / Export':
            continue

        # Disregard substantially negative values, but let slightly negative values through
        if value < -1:
            logger.warning('Skipping %s because production can\'t be negative (%s)' % (station, value))
            continue

        # Parse the datetime and check it matches the most recent one.
        try:
            plant_timestamp = arrow.get(row['Most Recent Output Time (AEST)']).datetime
        except (OSError, ValueError):
            # ignore invalid dates, they might be parsed as NaN
            continue
        else:
            # if plant_timestamp could be parsed successfully,
            # check plant_timestamp equals latest_timestamp and drop plant otherwise
            if plant_timestamp != data['datetime']:
                continue

        # Initialize key in data dictionaries if not set
        if key not in data['production']:
            data['production'][key] = 0.0
        if key not in data['capacity']:
            data['capacity'][key] = 0.0

        data['production'][key] += value
        data['capacity'][key] += float(row['Max Cap (MW)'])
        data['production'][key] = max(data['production'][key], 0)
        data['capacity'][key] = max(data['capacity'][key], 0)

    # find distributed solar production and add it in
    session = session or requests.session()
    distributed_solar_production = AU_solar.fetch_solar_for_date(zone_key, data['datetime'],
                                                                 session)
    if distributed_solar_production:
        data['production']['solar'] = (data['production'].get('solar', 0) +
                                       distributed_solar_production)

    if zone_key == 'AUS-SA':
        # Get South Australia battery status.
        data['storage']['battery'] = AU_battery.fetch_SA_battery()

    return data


# It appears that the interconnectors are named according to positive flow.
# That is, NSW1-QLD1 reports positive values when there is flow from NSW to QLD,
# and negative values when flow is from QLD to NSW.
# To verify, compare with flows shown on
# http://aemo.com.au/Electricity/National-Electricity-Market-NEM/Data-dashboard#nem-dispatch-overview
EXCHANGE_MAPPING_DICTIONARY = {
    'AUS-NSW->AUS-QLD': {
        'region_id': 'QLD1',
        'interconnector_names': ['N-Q-MNSP1', 'NSW1-QLD1'],
        'directions': [1, 1]
    },
    'AUS-NSW->AUS-VIC': {
        'region_id': 'NSW1',
        'interconnector_names': ['VIC1-NSW1'],
        'directions': [-1]
    },
    'AUS-SA->AUS-VIC': {
        'region_id': 'VIC1',
        'interconnector_names': ['V-SA', 'V-S-MNSP1'],
        'directions': [-1, -1]
    },
    'AUS-TAS->AUS-VIC': {
        'region_id': 'VIC1',
        'interconnector_names': ['T-V-MNSP1'],
        'directions': [1]
    },
}


def fetch_exchange(zone_key1=None, zone_key2=None, session=None, target_datetime=None,
                   logger=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedZoneKeys': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sorted_zone_keys = '->'.join(sorted([zone_key1, zone_key2]))
    mapping = EXCHANGE_MAPPING_DICTIONARY[sorted_zone_keys]

    r = session or requests.session()
    url = 'https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY'
    response = r.get(url)
    obj = list(filter(lambda o: o['REGIONID'] == mapping['region_id'],
                      response.json()['ELEC_NEM_SUMMARY']))[0]

    flows = json.loads(obj['INTERCONNECTORFLOWS'])
    net_flow = 0
    import_capacity = 0
    export_capacity = 0
    for i in range(len(mapping['interconnector_names'])):
        interconnector_name = mapping['interconnector_names'][i]
        interconnector = list(filter(lambda f: f['name'] == interconnector_name, flows))[0]
        direction = mapping['directions'][i]
        net_flow += direction * interconnector['value']
        import_capacity += direction * interconnector[
            'importlimit' if direction == 1 else 'exportlimit']
        export_capacity += direction * interconnector[
            'exportlimit' if direction == 1 else 'importlimit']

    data = {
        'sortedZoneKeys': sorted_zone_keys,
        'netFlow': net_flow,
        'capacity': [import_capacity, export_capacity],  # first one should be negative
        'source': 'aemo.com.au',
        'datetime': arrow.get(arrow.get(obj['SETTLEMENTDATE']).datetime, 'Australia/NSW').replace(
            minutes=-5).datetime
    }

    return data


PRICE_MAPPING_DICTIONARY = {
    'AUS-NSW': 'NSW1',
    'AUS-QLD': 'QLD1',
    'AUS-SA': 'SA1',
    'AUS-TAS': 'TAS1',
    'AUS-VIC': 'VIC1',
}


def fetch_price(zone_key=None, session=None, target_datetime=None, logger=None):
    """Requests the last known power price of a given country

    Arguments:
    zone_key (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'zoneKey': 'FR',
      'currency': 'EUR',
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY'
    response = r.get(url)
    obj = list(filter(lambda o:
                      o['REGIONID'] == PRICE_MAPPING_DICTIONARY[zone_key],
                      response.json()['ELEC_NEM_SUMMARY']))[0]

    data = {
        'zoneKey': zone_key,
        'currency': 'AUD',
        'price': obj['PRICE'],
        'source': 'aemo.com.au',
        'datetime': arrow.get(arrow.get(obj['SETTLEMENTDATE']).datetime, 'Australia/NSW').replace(
            minutes=-5).datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production("AUS-NSW") ->')
    print(fetch_production('AUS-NSW'))
    print('fetch_production("AUS-QLD") ->')
    print(fetch_production('AUS-QLD'))
    print('fetch_production("AUS-SA") ->')
    print(fetch_production('AUS-SA'))
    print('fetch_production("AUS-TAS") ->')
    print(fetch_production('AUS-TAS'))
    print('fetch_production("AUS-VIC") ->')
    print(fetch_production('AUS-VIC'))
    # print("fetch_exchange('AUS-NSW', 'AUS-QLD') ->")
    # print(fetch_exchange('AUS-NSW', 'AUS-QLD'))
    # print("fetch_exchange('AUS-NSW', 'AUS-VIC') ->")
    # print(fetch_exchange('AUS-NSW', 'AUS-VIC'))
    # print("fetch_exchange('AUS-VIC', 'AUS-SA') ->")
    # print(fetch_exchange('AUS-VIC', 'AUS-SA'))
    # print("fetch_exchange('AUS-VIC', 'AUS-TAS') ->")
    # print(fetch_exchange('AUS-VIC', 'AUS-TAS'))
