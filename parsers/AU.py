# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests

import json
import pandas as pd
import math

AMEO_CATEGORY_DICTIONARY = {
    'Bagasse': 'biomass',
    'Black Coal': 'coal',
    'Brown Coal': 'coal',
    'coal': 'coal',
    'Coal Seam Methane': 'gas',
    'Diesel': 'oil',
    'gas': 'gas',
    'Macadamia Nut Shells': 'biomass',
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
  'Cathedral Rocks Wind Farm':  'AUS-SA',
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
  'Hazelwood Power Station': None, # Closed
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
  'Northern Power Station': None, # Closed
  'Nyngan Solar Plant': 'AUS-NSW',
  'Oakey Power Station': 'AUS-QLD',
  'Oaklands Hill Wind Farm': 'AUS-VIC',
  'Oaky Creek 2 Waste Coal Mine Gas Power Station Units 1-15': 'AUS-QLD',
  'Oaky Creek  Power Station': 'AUS-QLD',
  'Osborne Power Station': 'AUS-SA',
  'Paloona Power Station': 'AUS-TAS',
  'Pedler Creek Landfill Gas Power Station Units 1-3': 'AUS-SA',
  'Pindari Hydro Power Station': 'AUS-NSW',
  'Playford B Power Station': None, # Closed
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
  'Woodlawn Wind Farm':  'AUS-NSW',
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


def fetch_production(country_code=None, session=None):
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
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
    url = 'http://services.aremi.nationalmap.gov.au/aemo/v3/csv/all'
    df = pd.read_csv(url)
    data = {
        'countryCode': country_code,
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
        'source': 'aremi.nationalmap.gov.au',
    }
    for rowIndex, row in df.iterrows():
        if row['Most Recent Output Time (AEST)'] == '-': continue
        fuelsource = row['Fuel Source - Descriptor']
        station = row['Station Name']

        if station not in AMEO_LOCATION_DICTIONARY:
            print 'WARNING: station %s does not belong to any state' % station
            continue

        if AMEO_LOCATION_DICTIONARY[station] != country_code: continue

        if not fuelsource in AMEO_CATEGORY_DICTIONARY and not station in AMEO_STATION_DICTIONARY:
            # Only show warning if it actually produces something
            if float(row['Current Output (MW)']) if row['Current Output (MW)'] != '-' else 0.0:
                print 'WARNING: key %s is not supported' % fuelsource
                print row
            continue

        # Skip HVDC links
        if AMEO_CATEGORY_DICTIONARY.get(station, None) == 'Import / Export':
            continue

        key = AMEO_CATEGORY_DICTIONARY.get(fuelsource, None) or \
            AMEO_STATION_DICTIONARY.get(station)
        if row['Current Output (MW)'] != '-' and not math.isnan(row['Current Output (MW)']):
            value = float(row['Current Output (MW)'])
        else:
            value = 0.0

        # Check for negativity, but not too much
        if value < -1:
            print 'Skipping because production can\'t be negative (%s)' % value
            print row
            continue
        
        if not key in data['production']: data['production'][key] = 0.0
        if not key in data['capacity']: data['capacity'][key] = 0.0
        data['production'][key] += value
        data['capacity'][key] += float(row['Max Cap (MW)'])
        data['production'][key] = max(data['production'][key], 0)
        data['capacity'][key] = max(data['capacity'][key], 0)
        
        # Parse the datetime and return a python datetime object
        datetime = None
        try:
            datetime = arrow.get(row['Most Recent Output Time (AEST)']).datetime
        except:
            continue
        # TODO: We should check it's not too old..
        if not 'datetime' in data:
            data['datetime'] = datetime
        else:
            data['datetime'] = max(datetime, data['datetime'])

    return data


EXCHANGE_MAPPING_DICTIONARY = {
    'AUS-NSW->AUS-QLD': {
        'region_id': 'QLD1',
        'interconnector_names': ['N-Q-MNSP1', 'NSW1-QLD1'],
        'directions': [-1, -1]
    },
    'AUS-NSW->AUS-VIC': {
        'region_id': 'NSW1',
        'interconnector_names': ['VIC1-NSW1'],
        'directions': [1]
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


def fetch_exchange(country_code1=None, country_code2=None, session=None):
    """Requests the last known power exchange (in MW) between two countries

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'sortedCountryCodes': 'DK->NO',
      'datetime': '2017-01-01T00:00:00Z',
      'netFlow': 0.0,
      'source': 'mysource.com'
    }
    """

    sorted_country_codes = '->'.join(sorted([country_code1, country_code2]))
    mapping = EXCHANGE_MAPPING_DICTIONARY[sorted_country_codes]

    r = session or requests.session()
    url = 'https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY'
    response = r.get(url)
    obj = filter(
        lambda o: o['REGIONID'] == mapping['region_id'],
        response.json()['ELEC_NEM_SUMMARY'])[0]

    flows = json.loads(obj['INTERCONNECTORFLOWS'])
    netFlow = 0
    importCapacity = 0
    exportCapacity = 0
    for i in range(len(mapping['interconnector_names'])):
        interconnector_name = mapping['interconnector_names'][i]
        interconnector = filter(lambda f: f['name'] == interconnector_name, flows)[0]
        direction = mapping['directions'][i]
        netFlow += direction * interconnector['value']
        importCapacity += direction * interconnector['importlimit' if direction == 1 else 'exportlimit']
        exportCapacity += direction * interconnector['exportlimit' if direction == 1 else 'importlimit']

    data = {
        'sortedCountryCodes': sorted_country_codes,
        'netFlow': netFlow,
        'capacity': [importCapacity, exportCapacity], # first one should be negative
        'source': 'aemo.com.au',
        'datetime': arrow.get(arrow.get(obj['SETTLEMENTDATE']).datetime, 'Australia/NSW').replace(minutes=-5).datetime
    }

    return data


PRICE_MAPPING_DICTIONARY = {
    'AUS-NSW': 'NSW1',
    'AUS-QLD': 'QLD1',
    'AUS-SA':  'SA1',
    'AUS-TAS': 'TAS1',
    'AUS-VIC': 'VIC1',
}


def fetch_price(country_code=None, session=None):
    """Requests the last known power price of a given country

    Arguments:
    country_code (optional) -- used in case a parser is able to fetch multiple countries
    session (optional)      -- request session passed in order to re-use an existing session

    Return:
    A dictionary in the form:
    {
      'countryCode': 'FR',
      'currency': EUR,
      'datetime': '2017-01-01T00:00:00Z',
      'price': 0.0,
      'source': 'mysource.com'
    }
    """

    r = session or requests.session()
    url = 'https://www.aemo.com.au/aemo/apps/api/report/ELEC_NEM_SUMMARY'
    response = r.get(url)
    obj = filter(
        lambda o: o['REGIONID'] == PRICE_MAPPING_DICTIONARY[country_code],
        response.json()['ELEC_NEM_SUMMARY'])[0]

    data = {
        'countryCode': country_code,
        'currency': 'AUD',
        'price': obj['PRICE'],
        'source': 'aemo.com.au',
        'datetime': arrow.get(arrow.get(obj['SETTLEMENTDATE']).datetime, 'Australia/NSW').replace(minutes=-5).datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production("AUS-NSW") ->'
    print fetch_production('AUS-NSW')
    print 'fetch_production("AUS-QLD") ->'
    print fetch_production('AUS-QLD')
    print 'fetch_production("AUS-SA") ->'
    print fetch_production('AUS-SA')
    print 'fetch_production("AUS-TAS") ->'
    print fetch_production('AUS-TAS')
    print 'fetch_production("AUS-VIC") ->'
    print fetch_production('AUS-VIC')
    # print "fetch_exchange('AUS-NSW', 'AUS-QLD') ->"
    # print fetch_exchange('AUS-NSW', 'AUS-QLD')
    # print "fetch_exchange('AUS-NSW', 'AUS-VIC') ->"
    # print fetch_exchange('AUS-NSW', 'AUS-VIC')
    # print "fetch_exchange('AUS-VIC', 'AUS-SA') ->"
    # print fetch_exchange('AUS-VIC', 'AUS-SA')
    # print "fetch_exchange('AUS-VIC', 'AUS-TAS') ->"
    # print fetch_exchange('AUS-VIC', 'AUS-TAS')
