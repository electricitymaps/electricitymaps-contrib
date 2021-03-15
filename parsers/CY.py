#!/usr/bin/env python3
import logging
import datetime
import sys

# The arrow library is used to handle datetimes
import arrow
# The request library is used to fetch content through HTTP
import requests
# BeautifulSoup is used to parse HTML
from bs4 import BeautifulSoup

class CyprusParser:
    CAPACITY_KEYS = {
        'Συμβατική Εγκατεστημένη Ισχύς': 'oil',
        'Αιολική Εγκατεστημένη Ισχύς': 'wind',
        'Φωτοβολταϊκή Εγκατεστημένη Ισχύς': 'solar',
        'Εγκατεστημένη Ισχύς Βιομάζας': 'biomass'
    }

    session = None
    logger: logging.Logger = None

    def __init__(self, session, logger: logging.Logger):
        self.session = session
        self.logger = logger

    def warn(self, text: str) -> None:
        self.logger.warning(text, extra={'key': 'CY'})

    def parse_capacity(self, html) -> dict:
        capacity = {}
        table = html.find(id='production_graph_static_data')
        for tr in table.find_all('tr'):
            values = [td.string for td in tr.find_all('td')]
            key = self.CAPACITY_KEYS.get(values[0])
            if key:
                capacity[key] = float(values[1])
        return capacity

    def parse_production(self, html, capacity: dict) -> list:
        data = []
        table = html.find(id='production_graph_data')
        columns = [th.string for th in table.find_all('th')]
        midnight_biomass = 0.0
        for tr in table.tbody.find_all('tr'):
            values = [td.string for td in tr.find_all('td')]
            if None in values or '' in values:
                break
            production = {}
            datum = {
                'zoneKey': 'CY',
                'production': production,
                'capacity': capacity,
                'storage': {},
                'source': 'tsoc.org.cy'
            }
            for col, val in zip(columns, values):
                if col == 'Timestamp':
                    datum['datetime'] = arrow.get(val).replace(tzinfo='Asia/Nicosia').datetime
                elif col == 'Αιολική Παραγωγή':
                    production['wind'] = float(val)
                elif col == 'Συμβατική Παραγωγή':
                    production['oil'] = float(val)
                elif col == 'Εκτίμηση Διεσπαρμένης Παραγωγής (Φωτοβολταϊκά και Βιομάζα)':
                    # Because solar is explicitly listed as "Solar PV" (so no thermal with energy storage) and there
                    # is zero sunlight in the middle of the night (https://www.timeanddate.com/sun/cyprus/nicosia),
                    # we use the biomass+solar generation reported at 0:00 to determine the portion of biomass+solar
                    # which constitutes biomass
                    if len(data) == 0:
                        midnight_biomass = float(val)
                        production['biomass'] = midnight_biomass
                        production['solar'] = 0.0
                    else:
                        production['biomass'] = midnight_biomass
                        production['solar'] = float(val) - midnight_biomass
            data.append(datum)
        return data

    def fetch_production(self, target_datetime: datetime.datetime) -> list:
        if target_datetime is None:
            url = 'https://tsoc.org.cy/electrical-system/total-daily-system-generation-on-the-transmission-system/'
        else:
            # convert target datetime to local datetime
            url_date = arrow.get(target_datetime).to('Asia/Nicosia').format('DD-MM-YYYY')
            url = f'https://tsoc.org.cy/electrical-system/archive-total-daily-system-generation-on-the-transmission-system/?startdt={url_date}&enddt=%2B1days'

        res = self.session.get(url)
        assert res.status_code == 200, f'CY parser: GET {url} returned {res.status_code}'

        html = BeautifulSoup(res.text, 'lxml')

        capacity = self.parse_capacity(html)
        data = self.parse_production(html, capacity)

        if len(data) == 0:
            self.warn('No production data returned for Cyprus')
        return data

def fetch_production(zone_key='CY', session=None,
        target_datetime: datetime.datetime = None,
        logger: logging.Logger = logging.getLogger(__name__)) -> list:
    """Requests the last known production mix (in MW) of a given country

    Arguments:
    ----------
    zone_key: used in case a parser is able to fetch multiple countries
    session: request session passed in order to re-use an existing session
    target_datetime: the datetime for which we want production data. If not
      provided, we should default it to now. If past data is not available,
      raise a NotImplementedError. Beware that the provided target_datetime is
      UTC. To convert to local timezone, you can use
      `target_datetime = arrow.get(target_datetime).to('America/New_York')`.
      Note that `arrow.get(None)` returns UTC now.
    logger: an instance of a `logging.Logger` that will be passed by the
      backend. Information logged will be publicly available so that correct
      execution of the logger can be checked. All Exceptions will automatically
      be logged, so when something's wrong, simply raise an Exception (with an
      explicit text). Use `logger.warning` or `logger.info` for information
      that can useful to check if the parser is working correctly. A default
      logger is used so that logger output can be seen when coding / debugging.

    Returns:
    --------
    If no data can be fetched, any falsy value (None, [], False) will be
      ignored by the backend. If there is no data because the source may have
      changed or is not available, raise an Exception.

    A dictionary in the form:

        {
            'zoneKey': 'FR',
            'datetime': '2017-01-01T00:00:00Z',
            'production': {
                'biomass': 0.0,
                'coal': 0.0,
                'gas': 0.0,
                'hydro': 0.0,
                'nuclear': None,
                'oil': 0.0,
                'solar': 0.0,
                'wind': 0.0,
                'geothermal': 0.0,
                'unknown': 0.0
            },
            'capacity': {
                'hydro': 500
            },
            'storage': {
                'hydro': -10.0,
            },
            'source': 'mysource.com'
        }
    """
    assert zone_key == 'CY'

    parser = CyprusParser(session or requests.session(), logger)
    return parser.fetch_production(target_datetime)


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy
    for testing."""

    target_datetime = None
    if len(sys.argv) == 4:
        target_datetime = datetime.datetime(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))

    print('fetch_production() ->')
    for datum in fetch_production(target_datetime=target_datetime):
        print(datum)
