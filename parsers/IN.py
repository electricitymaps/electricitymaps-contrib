# The arrow library is used to handle datetimes
from arrow import utcnow
# The request library is used to fetch content through HTTP
from requests import Session
from re import search, IGNORECASE


def fetch_consumption(country_code='IN', session=None):

    ses = session or session()

    url = "http://vidyutpravah.in/PXDashboard/BindTopStatisticsFromJS"
    response = ses.get(url)
    if response.status_code != 200 or not response.text:
        print '[WARNING]: IN Parser Response code:', response.status_code
        return None

    ## Extract demand from json
    json_response = response.json()
    dirty_demand = json_response[0].get('demand')
    clean_demand = search("<span class='counter'>(.*)</span><", dirty_demand, IGNORECASE).group(1)

    ## Convert GigaWatts to MegaWatts
    demand = round(float(clean_demand) * 1000, 2)
    print demand

    data = {
        'countryCode': country_code,
        'datetime': utcnow().datetime,
        'consumption': demand,
        'source': 'vidyutpravah.in'
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_consumption('IN', session)
