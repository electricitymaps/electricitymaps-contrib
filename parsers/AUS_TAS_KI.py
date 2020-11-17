# Initial PR https://github.com/tmrowco/electricitymap-contrib/pull/2456
# Discussion thread https://github.com/tmrowco/electricitymap-contrib/issues/636
# A promotion webpage for King's Island energy production is here : https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/king-island
# As of 09/2020, it embeds with <iframe> the URI https://data.ajenti.com.au/KIREIP/index.html
# About the data, the feed we get seems to be counters with a 2 seconds interval.
# That means that if we fetch these counters every 15 minutes, we only are reading "instantaneous" metters that could differ from the total quantity of energies at play. To get the very exact data, we would need to have a parser running constanty to collect those 2-sec interval counters.

import asyncio
import json
import logging
import arrow
from signalr import Connection
from requests import Session

class SignalR:
    def __init__(self, url):
        self.url = url
    
    def update_res(self, msg):
        if (msg != {}):
            self.res = msg

    def get_value(self, hub, method):
        self.res = {}
        with Session() as session:
            #create a connection
            connection = Connection(self.url, session)
            chat = connection.register_hub(hub)
            chat.client.on(method, self.update_res)
            connection.start()
            connection.wait(3)
            connection.close()
            return self.res
        
def parse_payload(logger, payload):
    technologies_parsed = {}
    if not 'technologies' in payload:
      raise KeyError(
        f"No 'technologies' in payload\n"
        f"serie : {json.dumps(payload)}"
      )
    else:
      logger.debug(f"serie : {json.dumps(payload)}")
    for technology in payload['technologies']:
        assert technology['unit'] == 'kW'
        # The upstream API gives us kW, we need MW
        technologies_parsed[technology['id']] = int(technology['value'])/1000
    logger.debug(f"production : {json.dumps(technologies_parsed)}")

    biodiesel_percent = payload['biodiesel']['percent']

    return technologies_parsed, biodiesel_percent

# Both keys battery and flywheel are negative when storing energy, and positive when feeding energy to the grid
def format_storage_techs(technologies_parsed):
    storage_techs = technologies_parsed['battery']+technologies_parsed['flywheel']
    battery_production = storage_techs if storage_techs > 0 else 0
    battery_storage = storage_techs if storage_techs < 0 else 0

    return battery_production, battery_storage

def fetch_production(zone_key='AUS-TAS-KI', session=None, target_datetime=None, logger: logging.Logger = logging.getLogger(__name__)):

    if target_datetime is not None:
        raise NotImplementedError('The datasource currently implemented is only real time')
      
    payload = SignalR("https://data.ajenti.com.au/live/signalr").get_value("TagHub", "Dashboard")
    technologies_parsed, biodiesel_percent = parse_payload(logger, payload)
    battery_production, battery_storage = format_storage_techs(technologies_parsed)
    return {
      'zoneKey': zone_key,
      'datetime': arrow.now(tz='Australia/Currie').datetime,
      'production': {
          'battery discharge': battery_production,
          'biomass': technologies_parsed['diesel']*biodiesel_percent/100,
          'coal': 0,
          'gas': 0,
          'hydro': 0,
          'nuclear': 0,
          'oil': technologies_parsed['diesel']*(100-biodiesel_percent)/100,
          'solar': technologies_parsed['solar'],
          'wind': 0 if technologies_parsed['wind'] < 0 and technologies_parsed['wind'] > -0.1 else technologies_parsed['wind'], #If wind between 0 and -0.1 set to 0 to ignore self-consumption
          'geothermal': 0,
          'unknown': 0
      },
      'storage': {
          'battery': battery_storage*-1
      },
      'source': 'https://data.ajenti.com.au/KIREIP/index.html'
    }

if __name__ == '__main__':
    print(fetch_production())
