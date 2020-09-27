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

def fetch_production(zone_key='AUS-TAS-KI', session=None, target_datetime=None, logger: logging.Logger = logging.getLogger(__name__)):

    if target_datetime is not None:
        raise NotImplementedError('The datasource currently implemented is only real time')
  
    if session is not None:
        # TODO : is that the best to do in our case ? (websockets)
        raise NotImplementedError
    
    payload = fetch_api()
    technologies_parsed, biodiesel_percent = parse_payload(logger, payload)

    """ 
    TODO
        * What do I return for production mode that are not even on the island ? 
            The main README says "The production values should never be negative. Use None, or omit the key if a specific production mode is not known." but doesn't answer this question
    """
    return {
      'zoneKey': zone_key,
      'datetime': arrow.now(tz='Australia/Currie').datetime,
      'production': {
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
          'battery': technologies_parsed['battery']*-1,
          'flywheel': technologies_parsed['flywheel']*-1,
      },
      'source': 'https://data.ajenti.com.au/KIREIP/index.html'
    }

if __name__ == '__main__':
    print(fetch_production())
