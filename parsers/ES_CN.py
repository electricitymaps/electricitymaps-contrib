# The arrow library is used to handle datetimes
from arrow import get
# The request library is used to fetch content through HTTP
from requests import Session
from reescraper import ElHierro, GranCanaria, Gomera, LanzaroteFuerteventura, LaPalma, Tenerife
from parsers.lib.exceptions import ParserException


def fetch_consumption(country_code='ES-CN', session=None):
    ses = session or Session()

    elhierro = ElHierro(ses).get()
    if not elhierro:
        raise ParserException("ES-CN", "ElHierro not response")

    granacanaria = GranCanaria(ses).get()
    if not granacanaria:
        raise ParserException("ES-CN", "GranCanaria not response")

    gomera = Gomera(ses).get()
    if not gomera:
        raise ParserException("ES-CN", "Gomera not response")

    lanzarotefuerteventura = LanzaroteFuerteventura(ses).get()
    if not lanzarotefuerteventura:
        raise ParserException("ES-CN", "LanzaroteFuerteventura not response")

    palma = LaPalma(ses).get()
    if not palma:
        raise ParserException("ES-CN", "LaPalma not response")

    tenerife = Tenerife(ses).get()
    if not tenerife:
        raise ParserException("ES-CN", "Tenerife not response")

    ## Compare timestamps
    ## Raise ParserException if timestamps aren't equals
    if elhierro.timestamp != granacanaria.timestamp \
        and elhierro.timestamp != gomera.timestamp \
        and elhierro.timestamp != lanzarotefuerteventura.timestamp \
        and elhierro.timestamp != palma.timestamp \
        and elhierro.timestamp != tenerife.timestamp:
        raise ParserException("ES-CN", "Response timestamps aren't equals")

    demand = round(elhierro.demand + granacanaria.demand + gomera.demand + lanzarotefuerteventura.demand + palma.demand + tenerife.demand, 2)

    data = {
        'countryCode': country_code,
        'datetime': get(elhierro.timestamp).datetime,
        'consumption': demand,
        'source': 'demanda.ree.es'
    }

    return data


def fetch_production(country_code='ES-CN', session=None):
    ses = session or Session()

    elhierro = ElHierro(ses).get()
    if not elhierro:
        raise ParserException("ES-CN", "ElHierro not response")

    granacanaria = GranCanaria(ses).get()
    if not granacanaria:
        raise ParserException("ES-CN", "GranCanaria not response")

    gomera = Gomera(ses).get()
    if not gomera:
        raise ParserException("ES-CN", "Gomera not response")

    lanzarotefuerteventura = LanzaroteFuerteventura(ses).get()
    if not lanzarotefuerteventura:
        raise ParserException("ES-CN", "LanzaroteFuerteventura not response")

    palma = LaPalma(ses).get()
    if not palma:
        raise ParserException("ES-CN", "LaPalma not response")

    tenerife = Tenerife(ses).get()
    if not tenerife:
        raise ParserException("ES-CN", "Tenerife not response")

    ## Compare timestamps
    ## Raise ParserException if timestamps aren't equals
    if elhierro.timestamp != granacanaria.timestamp \
        and elhierro.timestamp != gomera.timestamp \
        and elhierro.timestamp != lanzarotefuerteventura.timestamp \
        and elhierro.timestamp != palma.timestamp \
        and elhierro.timestamp != tenerife.timestamp:
        raise ParserException("ES-CN", "Response timestamps aren't equals")

    ## Gas production
    gas_elhierro = elhierro.gas + elhierro.combined
    gas_granacanaria = granacanaria.gas + granacanaria.combined
    gas_gomera = gomera.gas + gomera.combined
    gas_lanzarotefuerteventura = lanzarotefuerteventura.gas + lanzarotefuerteventura.combined
    gas_palma = palma.gas + palma.combined
    gas_tenerife = tenerife.gas + tenerife.combined
    gas_total = gas_elhierro + gas_granacanaria + gas_gomera + gas_lanzarotefuerteventura + gas_palma + gas_tenerife

    ## Solar production
    solar_total = elhierro.solar + granacanaria.solar + gomera.solar + lanzarotefuerteventura.solar + palma.solar + tenerife.solar

    ## Oil production
    oil_elhierro = elhierro.vapor + elhierro.diesel
    oil_granacanaria = granacanaria.gas + granacanaria.combined
    oil_gomera = gomera.gas + gomera.combined
    oil_lanzarotefuerteventura = lanzarotefuerteventura.gas + lanzarotefuerteventura.combined
    oil_palma = palma.gas + palma.combined
    oil_tenerife = tenerife.gas + tenerife.combined
    oil_total = oil_elhierro + oil_granacanaria + oil_gomera + oil_lanzarotefuerteventura + oil_palma + oil_tenerife

    ## Wind production
    wind_total = elhierro.wind + granacanaria.wind + gomera.wind + lanzarotefuerteventura.wind + palma.wind + tenerife.wind

    ## Hydro production (EL Hierrro is exluded)
    hydro_total = granacanaria.hydraulic + gomera.hydraulic + lanzarotefuerteventura.hydraulic + palma.hydraulic + tenerife.hydraulic


    ## Hydro storage
    hydro_storage = -elhierro.hydraulic

    data = {
        'countryCode': country_code,
        'datetime': get(elhierro.timestamp).datetime,
        'production': {
            'coal': 0.0,
            'gas': round(gas_total, 2),
            'solar': round(solar_total, 2),
            'oil': round(oil_total, 2),
            'wind': round(wind_total, 2),
            'hydro': round(hydro_total, 2),
            'biomass': 0.0,
            'nuclear': 0.0,
            'geothermal': 0.0,
            'unknown': 0.0
        },
        'storage': {
            'hydro': round(hydro_storage, 2)
        },
        'source': 'demanda.ree.es',
    }

    return data


if __name__ == '__main__':
    session = Session
    print fetch_consumption('ES-CN', session)
    print fetch_production('ES-CN', session)
