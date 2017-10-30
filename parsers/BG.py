# encoding=utf8
# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
from bs4 import BeautifulSoup

TIME_ZONE = 'Europe/Sofia'
TYPE_MAPPING = {                        # Real values around midnight
    u'АЕЦ': 'nuclear',                  # 2000
    u'Кондензационни ТЕЦ': 'coal',      # 1800
    u'Топлофикационни ТЕЦ': 'gas',      # 146
    u'Заводски ТЕЦ': 'gas',             # 147
    u'ВЕЦ': 'hydro',                    # 7
    u'Малки ВЕЦ': 'hydro',              # 74
    u'ВяЕЦ': 'wind',                    # 488
    u'ФЕЦ': 'solar',                    # 0
    u'Био ТЕЦ': 'biomass',              # 29
    u'Товар РБ': 'consumption',         # 3175
}


def fetch_production(country_code='BG', session=None):
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
    r = session or requests.session()
    url = 'http://www.tso.bg/GeneratedPowersPublicExt/'
    response = r.get(url)
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # first compute the datetime
    datetime = None
    local_time = soup.find(id='lblTecDate')
    if local_time:
        time = local_time.string.split(':')
        if len(time) == 3:
            datetime = arrow.now('Europe/Sofia').floor('day').\
                replace(hour=int(time[0]), minute=int(time[1]), second=int(time[2]))

    if not datetime:
        raise Exception('No datetime')

    # then populate an object that contains the consumptions by type, we will parse a table something like that
    # АЕЦ	1998
    # Кондензационни ТЕЦ	1790
    # Топлофикационни ТЕЦ	146
    # Заводски ТЕЦ	146
    # ВЕЦ	7
    # Малки ВЕЦ	72
    # ВяЕЦ	483
    # ФЕЦ	0
    # Био ТЕЦ	30
    # Товар РБ	3114

    res = dict()
    lines = soup.find_all('table')         # each line is in a <table>
    for l in lines:
        try:    # we want to read only values that have a non empty label and a non empty float value
            label = l.find('td')
            value = l.find('span')
            if value and label:
                energy_type = TYPE_MAPPING.get(label.string.strip(), 'unknown')
                res[energy_type] = res.get(energy_type, 0.0) + float(value.string)
        except (TypeError, ValueError), e:
            print str(e)
            pass    # this ensure we skip lines that have no float value

    data = {
        'countryCode': 'BG',
        'production': {
            'biomass': res.get('biomass', 0.0),
            'hydro': res.get('hydro', 0.0),
            'nuclear': res.get('nuclear', 0.0),
            'wind': res.get('wind', 0.0),
            'coal': res.get('coal', 0.0),
            'solar': res.get('solar', 0.0),
            'gas': res.get('gas', 0.0),
            'unknown': res.get('unknown', 0.0)
        },
        'storage': {},
        'source': 'tso.bg',
        'datetime': datetime.datetime
    }

    return data


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print 'fetch_production() ->'
    print fetch_production()
