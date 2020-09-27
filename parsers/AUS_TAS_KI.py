# Initial PR https://github.com/tmrowco/electricitymap-contrib/pull/2456
# Discussion thread https://github.com/tmrowco/electricitymap-contrib/issues/636
# This parser is clumsy ; we are parsing an interface that's not meant for that
# and with the wrong tools.
# A promotion webpage for King's Island energy production is here : https://www.hydro.com.au/clean-energy/hybrid-energy-solutions/success-stories/king-island
# As of 09/2020, it embeds with <iframe> the URI https://data.ajenti.com.au/KIREIP/index.html
# From that page we find references to SignalR technologies, but as I couldn't get a SignalR client to work, I'm scraping like a beast.
# About the data, the feed we get seems to be counters with a 2 seconds interval.
# That means that if we fetch these counters every 15 minutes, we only are reading "instantaneous" metters that could differ from the total quantity of energies at play. To get the very exact data, we would need to have a parser running constanty to collect those 2-sec interval counters.
import asyncio
import websockets
import json
import logging
import arrow

technologies_parsed = {}

def fetch_api():
    async def fetch():
        # TODO this is likely not a viable endpoint / way to fetch this
        # As this URI contains an hardcoded token that eventually expires, 
        # note that you can get that URI from https://data.ajenti.com.au/KIREIP/index.html
        # by looking at the console logs. You'll see a "/connect" route that you can insert here, it'll fail, you'll get a /reconnect route that will then works. 
        # Please don't ask me why
        uri = "wss://data.ajenti.com.au/live/signalr/reconnect?transport=webSockets&messageId=d-7971CA90-Bmk%2C12C%7CBms%2C0%7CBmt%2C1&clientProtocol=1.5&connectionToken=09ZTjbJpmUNdevf8JNLMlnTL6lOh6Qc8n6dWYtnbP%2FicpI05qDWeZ9fRQFj%2FmbdVVL1vHMRYpGfB9PAORwWXMepVOLGsDvH4gqPNcrMdHpPdDmO3isKxxisvgnWdClUK&connectionData=%5B%7B%22name%22%3A%22taghub%22%7D%5D&tid=6"
        async with websockets.connect(uri) as websocket:
            payload_str = await websocket.recv()
            payload = json.loads(payload_str)
            return payload

    # Sometimes the webservice returns an empty dic (in ~20% of the calls)... Let's retry two times in those cases
    res = {}
    tries = 0
    while res == {} and tries < 2:
        res = asyncio.get_event_loop().run_until_complete(fetch())
        tries+=1
    return res

def parse_payload(logger, payload):
    for message in payload['M']:
        for serie in message['A']:
            logger.debug(f"serie : {json.dumps(serie)}")
            for technology in serie['technologies']:
                assert technology['unit'] == 'kW'
                # The upstream API gives us kW, we need MW
                technologies_parsed[technology['id']] = int(technology['value'])/1000
            logger.debug(f"production : {json.dumps(technologies_parsed)}")

            biodiesel_percent = serie['biodiesel']['percent']


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
  
    if session is not None:
        # TODO : is that the best to do in our case ? (websockets)
        raise NotImplementedError
    
    payload = fetch_api()
    technologies_parsed, biodiesel_percent = parse_payload(logger, payload)
    battery_production, battery_storage = format_storage_techs(technologies_parsed)
    return {
      'zoneKey': zone_key,
      'datetime': arrow.now(tz='Australia/Currie').datetime,
      'production': {
          'battery': battery_storage,
          'biomass': technologies_parsed['diesel']*biodiesel_percent/100,
          'coal': 0,
          'gas': 0,
          'hydro': 0,
          'nuclear': 0,
          'oil': technologies_parsed['diesel']*(100-biodiesel_percent)/100,
          'solar': technologies_parsed['solar'],
          'wind': technologies_parsed['wind'],
          'geothermal': 0,
          'unknown': 0
      },
      'storage': {
          'battery': battery_production*-1
      },
      'source': 'https://data.ajenti.com.au/KIREIP/index.html'
    }

if __name__ == '__main__':
    print(fetch_production())
