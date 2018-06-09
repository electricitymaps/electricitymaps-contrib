#!/usr/bin/env python3

import logging
from arrow import get
from requests import Session
from ree import (Formentera, Ibiza,
                 Mallorca, Menorca,
                 BalearicIslands, IberianPeninsula)

## I had to comment these two due to local issues:

#from .lib.exceptions import ParserException
#from .lib.validation import validate

## Guess we'll need to figure these out later?! Adapted from ES-CN:

# Minimum valid zone demand. This is used to eliminate some cases
# where generation for one or more modes is obviously missing.
#FLOORS = {
#'ES-IB-FO': 0,
#'ES-IB-IZ': 0,
#'ES-IB-MA': 0,
#'ES-IB-ME': 0,
#}


def fetch_island_data(zone_key, session):
    if zone_key == 'ES-IB-FO':
        formentera_data = Formentera(session, verify=False).get_all()
        if not formentera_data:
            raise ParserException(zone_key, "Formentera doesn't respond")
        else:
            return formentera_data
    elif zone_key == 'ES-IB-IZ':
        ibiza_data = Ibiza(session, verify=False).get_all()
        if not ibiza_data:
            raise ParserException(zone_key, "Party is over, Ibiza doesn't respond")
        else:
            return ibiza_data
    elif zone_key == 'ES-IB-MA':
        mallorca_data = Mallorca(session, verify=False).get_all()
        if not mallorca_data:
            raise ParserException(zone_key, "Mallorca doesn't respond")
        else:
            return mallorca_data
    elif zone_key == 'ES-IB-ME':
        menorca_data = Menorca(session, verify=False).get_all()
        if not menorca_data:
            raise ParserException(zone_key, "Menorca doesn't respond")
        else:
            return menorca_data
    else:
        raise ParserException(zone_key, 'Can\'t read this country code {0}'.format(zone_key))


def fetch_consumption(zone_key, session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')
    
    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []
    for response in island_data:
        response_data = {
            'zoneKey': zone_key,
            'datetime': get(response.timestamp).datetime,
            'consumption': response.demand,
            'source': 'demanda.ree.es'
        }

        data.append(response_data)

    return data


def fetch_production(zone_key, session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    ses = session or Session()
    island_data = fetch_island_data(zone_key, ses)
    data = []

## biomass could probably be added as response.biomass in ree, including value['resid'] which I assume is for residuos=waste. Atm it seems unincluded.
## I saw generation from "genAux" (generacion auxiliar) today on Formentera, which should probably be added to response.other in ree
## Formentera mostly only has some solar generation during the day, importing from Ibiza all of the time, which probably has to be considered for response.production() > 0: ?

    for response in island_data:
        if response.production() > 0:
            response_data = {
                'zoneKey': zone_key,
                'datetime': get(response.timestamp).datetime,
                'production': {
                'coal': response.carbon,
                'gas': round(response.gas + response.combined, 2),
                'solar': response.solar,
                'oil': round(response.vapor + response.diesel, 2),
                'wind': response.wind,
                'hydro': response.hydraulic,
                'biomass': 0.0,
                'nuclear': 0.0,
                'geothermal': 0.0,
                'unknown': response.other
            },
            'storage': {
                'hydro': 0.0,
                'battery': 0.0
            },
            'source': 'demanda.ree.es',
        }

## I had to comment the validation due to local issues and the commented FLOORS from above:

#                response_data = validate(response_data, logger,
#                                         floor=FLOORS[zone_key])
#
#                if response_data:
#                    # append if valid
#                    data.append(response_data)
            data.append(response_data) ## delete this line when you uncomment the lines right above

    return data


def fetch_exchange(zone_key1, zone_key2, session=None, target_datetime=None, logger=None):

    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))

    ses = session or Session()
    response_ma = Mallorca(ses, verify=False).get_all()
    response_fo = Formentera(ses, verify=False).get_all()

    if not response_ma:
        raise ParserException("ES-IB-MA", "No response")
    elif not response_fo:
        raise ParserException("ES-IB-FO", "No response")        
    else:
        if sortedZoneKeys == 'ES->ES-IB-MA':
            for response in response_ma:
                netflow = response.link['pe_ma']
        elif sortedZoneKeys == 'ES-IB-MA->ES-IB-ME':
            for response in response_ma:
                netflow = response.link['ma_me']
        elif sortedZoneKeys == 'ES-IB-IZ->ES-IB-MA':
            for response in response_ma:
                netflow = response.link['ma_ib']
        elif sortedZoneKeys == 'ES-IB-FO->ES-IB-IZ':
            for response in response_fo:
                netflow = -1 * response.link['ib_fo']
        else:
            raise NotImplementedError('This exchange pair is not implemented')

        exchange = {
            'sortedZoneKeys': sortedZoneKeys,
            'datetime': get(response.timestamp).datetime,
            'netFlow': netflow,
            'source': 'demanda.ree.es'
        }

    return exchange

session = Session
   
print("# ES-IB-FO")
print(fetch_consumption('ES-IB-FO', session))
print(fetch_production('ES-IB-FO', session))
print("# ES-IB-IZ")
print(fetch_consumption('ES-IB-IZ', session))
print(fetch_production('ES-IB-IZ', session))
print("# ES-IB-MA")
print(fetch_consumption('ES-IB-MA', session))
print(fetch_production('ES-IB-MA', session))
print("# ES-IB-ME")
print(fetch_consumption('ES-IB-ME', session))
print(fetch_production('ES-IB-ME', session))
print("# exchanges")
print(fetch_exchange('ES', 'ES-IB-MA', session))
print(fetch_exchange('ES-IB-MA', 'ES-IB-ME', session))
print(fetch_exchange('ES-IB-MA', 'ES-IB-IZ', session))
print(fetch_exchange('ES-IB-IZ', 'ES-IB-FO', session)) 
