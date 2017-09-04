from requests import Session
from arrow import get
from parsers import web
from parsers import countrycode


def fetch_production(country_code='IN-KA', session=None):
    """Fetch Karnataka  production"""
    countrycode.assert_country_code(country_code, 'IN-KA')

    html = web.get_response_soup(country_code, 'http://kptclsldc.com/StateGen.aspx', session)

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
