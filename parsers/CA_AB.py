
import arrow
from bs4 import BeautifulSoup
import datetime
import re
import requests
import pandas as pd
from pytz import timezone

ab_timezone = 'Canada/Mountain'


def convert_time_str(ts):
    """Takes a time string and converts into an aware datetime object."""

    dt_naive = datetime.datetime.strptime(ts, ' %b %d, %Y %H:%M')
    localtz = timezone('Canada/Mountain')
    dt_aware = localtz.localize(dt_naive)

    return dt_aware


def fetch_production(zone_key='CA-AB', session=None, target_datetime=None, logger=None):
    """
    Requests the last known production mix (in MW) of a given country.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet'
    response = r.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    findtime = soup.find('td', text=re.compile('Last Update')).get_text()
    time_string = findtime.split(':', 1)[1]
    dt = convert_time_str(time_string)

    df_generations = pd.read_html(response.text, match='GENERATION', skiprows=1, index_col=0, header=0)

    for idx, df in enumerate(df_generations):
        try:
            total_net_generation = df_generations[idx]['TNG']
            maximum_capability = df_generations[idx]['MC']
        except KeyError:
            continue

    return {
        'datetime': dt,
        'zoneKey': zone_key,
        'production': {
            'coal': float(total_net_generation['COAL']),
            'gas': float(total_net_generation['GAS']),
            'hydro': float(total_net_generation['HYDRO']),
            'wind': float(total_net_generation['WIND']),
            'unknown': float(total_net_generation['OTHER'])
        },
        'capacity': {
            'coal': float(maximum_capability['COAL']),
            'gas': float(maximum_capability['GAS']),
            'hydro': float(maximum_capability['HYDRO']),
            'wind': float(maximum_capability['WIND']),
            'unknown': float(maximum_capability['OTHER'])
        },
        'source': 'ets.aeso.ca',
    }


def fetch_price(zone_key='CA-AB', session=None, target_datetime=None, logger=None):
    """
    Requests the last known power price of a given country.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://ets.aeso.ca/ets_web/ip/Market/Reports/SMPriceReportServlet?contentType=html/'
    response = r.get(url)

    df_prices = pd.read_html(response.text, match='Price', index_col=0, header=0)
    prices = df_prices[1]

    data = {}

    for rowIndex, row in prices.iterrows():
        price = row['Price ($)']
        if (isfloat(price)):
            hour = int(rowIndex.split(' ')[1]) - 1
            data[rowIndex] = {
                'datetime': arrow.get(rowIndex, 'MM/DD/YYYY').replace(hour=hour, tzinfo=ab_timezone).datetime,
                'zoneKey': zone_key,
                'currency': 'CAD',
                'source': 'ets.aeso.ca',
                'price': float(price),
            }

    return [data[k] for k in sorted(data.keys())]


def fetch_exchange(zone_key1='CA-AB', zone_key2='CA-BC', session=None, target_datetime=None, logger=None):
    """
    Requests the last known power exchange (in MW) between two countries.
    """
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    r = session or requests.session()
    url = 'http://ets.aeso.ca/ets_web/ip/Market/Reports/CSDReportServlet'
    response = r.get(url)
    df_exchanges = pd.read_html(response.text, match='INTERCHANGE', skiprows=0, index_col=0)

    flows = {
        'CA-AB->CA-BC': df_exchanges[1][1]['British Columbia'],
        'CA-AB->CA-SK': df_exchanges[1][1]['Saskatchewan'],
        'CA-AB->US-MT': df_exchanges[1][1]['Montana'],
        'CA-AB->US-NW-NWMT': df_exchanges[1][1]['Montana']
    }
    sortedZoneKeys = '->'.join(sorted([zone_key1, zone_key2]))
    if sortedZoneKeys not in flows:
        raise NotImplementedError('This exchange pair is not implemented')

    return {
        'datetime': arrow.now(tz=ab_timezone).datetime,
        'sortedZoneKeys': sortedZoneKeys,
        'netFlow': float(flows[sortedZoneKeys]),
        'source': 'ets.aeso.ca'
    }


def isfloat(value):
    try:
      float(value)
      return True
    except ValueError:
      return False


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_production() ->')
    print(fetch_production())
    print('fetch_price() ->')
    print(fetch_price())
    print('fetch_exchange(CA-AB, CA-BC) ->')
    print(fetch_exchange('CA-AB', 'CA-BC'))
    print('fetch_exchange(CA-AB, CA-SK) ->')
    print(fetch_exchange('CA-AB', 'CA-SK'))
    print('fetch_exchange(CA-AB, US-MT) ->')
    print(fetch_exchange('CA-AB', 'US-MT'))
