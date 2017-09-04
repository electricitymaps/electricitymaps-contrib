from requests import Session
from arrow import get
from bs4 import BeautifulSoup


def fetch_production(country_code='IN-KA', session=None):
    """Fetch Karnataka  production"""
    if not country_code and country_code != 'IN-KA':
        raise Exception('IN-KA Parser country_code isn\'t IN-KA')

    ses = session or Session()
    response = ses.get('http://kptclsldc.com/StateGen.aspx')
    if response.status_code != 200:
        raise Exception('IN-KA Parser Response code: {0}'.format(response.status_code))
    if not response.text:
        raise Exception('IN-KA Parser Response empty')

    html = BeautifulSoup(response.text, 'html.parser')

    date_time_span = html.find('span', {'id': 'lbldate'})
    india_date_time_text = date_time_span.text + ' Asia/Kolkata'
    india_date_time = get(india_date_time_text, 'D/M/YYYY h:mm:ss A ZZZ')

    # State Production
    state_span = html.find('span', {'id': 'lblstategen'})
    state_value = float(state_span.text)

    # CGS Production
    cgs_span = html.find('span', {'id': 'lblcgs'})
    cgs_value = float(cgs_span.text)

    # NCEP Production
    ncep_span = html.find('span', {'id': 'lblncep'})
    ncep_value = float(ncep_span.text)

    unknown_value = round(cgs_value + ncep_value + state_value, 2)

    data = {
        'countryCode': country_code,
        'datetime': india_date_time.datetime,
        'production': {
            'biomass': 0.0,
            'coal': 0.0,
            'gas': 0.0,
            'hydro': 0.0,
            'nuclear': 0.0,
            'oil': 0.0,
            'solar': 0.0,
            'wind': 0.0,
            'geothermal': 0.0,
            'unknown': unknown_value
        },
        'storage': {
            'hydro': 0.0
        },
        'source': 'kptclsldc.com',
    }

    return data


if __name__ == '__main__':
    session = Session()
    print fetch_production('IN-KA', session)
