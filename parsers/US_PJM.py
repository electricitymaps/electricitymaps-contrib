# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests


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

    # PJM realtime data is here http://www.pjm.com/markets-and-operations.aspx
    r = session or requests.session()
    url = 'http://www.pjm.com/markets-and-operations.aspx'
    response = r.get(url)
    obj = response.json()

    data = {
        'countryCode': country_code,
        'production': {},
        'storage': {},
        'source': 'someservice.com',
    }
    for item in obj['productionMix']:
        # All production values should be >= 0
        data['production'][item['key']] = item['value'] # Should be a floating point value

    for item in obj['storage']:
        # Positive storage means energy is stored
        # Negative storage means energy is generated from the storage system
        data['storage'][item['key']] = item['value'] # Should be a floating point value

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data



def fetch_price(country_code='FR', session=None):
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

    # PJM realtime price data LMP is here (updates hourly)
        # (sub-regional) http://www.pjm.com/markets-and-operations/energy/real-time/lmp.aspx
        # (system aggregated average - RTO LMP 'locationalized marginal price') http://www.pjm.com/markets-and-operations.aspx
    r = session or requests.session()
    url = 'https://api.someservice.com/v1/price/latest'
    response = r.get(url)
    obj = response.json()

    data = {
        'countryCode': country_code,
        'currency': 'USD',
        'price': obj['price'],
        'source': 'someservice.com',
    }

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


def fetch_exchange(country_code1='US_PJM', country_code2='US_NY', country_code3='US_MISO', country_code3='US_TVA', session=None):
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

    # Realtime exchange flows are here... http://www.pjm.com/markets-and-operations/interregional-map.aspx
            # No. 1 - US-PJM->US-NY
                # to US_NY are combined from PJM (NYISO), PJM (Neptune), PJM (Linden) & PJM (Hudson)
            # No. 2 - US-PJM->TBD1
                # PJM (DOM - CPL Retail Energy East) to be determined, but a sub-state geometry
            # No. 3 - US-PJM->US_TBD2
                #PJM (AEP - Duke Energy) to be determined but likely a parser for NC & SC
            # No. 4 - US-PJM->US_TBD3
                # PJM (AEP - CPL Retail Energy West) to be determined, but a sub-state geometry
            # No. 5 - US-PJM->US-TVA
                # PJM (AEP - TVA), will be parser for US_TVA (Tennessee)
            # No. 6 - US-PJM->TBD4
                # PJM (EKPC - Louisville G&E Co), Kentucky geometry to be split in half --> Louisville is at the split
            # No. 7 - US-PJM->TBD5
                # PJM (DEOK - Ohio Valley Electric Co), to be determined, but likely a sub-state geometry
            # No. 8 - US-PJM->US-MISO
                # PJM (MISO) - MISO will be multiple state geometry with parser
            # No. 9 - US-NY->US-MISO
                # "Lake Erie Loop" is balancing for NYISO<-->IESO & MISO<-->IESO.
                # + MW for MISO (Michigan) equal - MW for NYISO,
                # passes thru PJM only, no balancing in PJM needed

    r = session or requests.session()
    url = 'https://api.someservice.com/v1/exchange/latest?from=%s&to=%s' % (country_code1, country_code2)
    response = r.get(url)
    obj = response.json()

    data = {
        'sortedCountryCodes': '->'.join(sorted([country_code1, country_code2])),
        'source': 'someservice.com',
    }

    # Country codes are sorted in order to enable easier indexing in the database
    sorted_country_codes = sorted([country_code1, country_code2])
    # Here we assume that the net flow returned by the api is the flow from
    # country1 to country2. A positive flow indicates an export from country1
    # to country2. A negative flow indicates an import.
    netFlow = obj['exchange']
    # The net flow to be reported should be from the first country to the second
    # (sorted alphabetically). This is NOT necessarily the same direction as the flow
    # from country1 to country2
    data['netFlow'] = netFlow if country_code1 == sorted_country_codes[0] else -1 * netFlow

    # Parse the datetime and return a python datetime object
    data['datetime'] = arrow.get(obj['datetime']).datetime

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
    print 'fetch_price() ->'
    print fetch_price()
    print 'fetch_exchange(DK, NO) ->'
    print fetch_exchange('DK', 'NO')
