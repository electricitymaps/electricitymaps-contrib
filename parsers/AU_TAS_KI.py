import asyncio
import websockets
import json
import logging
import arrow

technologies_parsed = {}

def fetch_api(logger):
    async def fetch():
        # TODO this is likely not a viable endpoint / way to fetch this
        uri = "wss://data.ajenti.com.au/live/signalr/reconnect?transport=webSockets&messageId=d-C8F39B96-km%2C152%7Ckr%2C0%7Cks%2C2&clientProtocol=1.5&connectionToken=Yu0BMoSk5rEBlaiSH%2BaLhoYTA3oiXDBcS%2FvqcVQr7q%2FnKYKbTppUSNS1Mz%2Bx1wwgH4VHAgSv5SalVBzsYrWiG92AM7r5qBJogpCJYS%2BqEWECTRQS%2BUl62HQ5UjFC6zCh&connectionData=%5B%7B%22name%22%3A%22taghub%22%7D%5D&tid=3"
        async with websockets.connect(uri) as websocket:
            payload_str = await websocket.recv()
            payload = json.loads(payload_str)
            for message in payload['M']:
                for serie in message['A']:
                    logger.debug(f"serie : {json.dumps(serie)}")
                    for technology in serie['technologies']:
                        assert technology['unit'] == 'kW'
                        # The upstream API gives us kW, we need MW
                        technologies_parsed[technology['id']] = int(technology['value'])/1000
                    logger.debug(f"production : {json.dumps(technologies_parsed)}")

    asyncio.get_event_loop().run_until_complete(fetch())
    return technologies_parsed

def fetch_production(zone_key='AUS-TAS-KI', session=None, target_datetime=None, logger: logging.Logger = logging.getLogger(__name__)):

    if target_datetime is not None:
        raise NotImplementedError('The datasource currently implemented is only real time')
  
    if session is not None:
        # TODO : is that the best to do in our case ? (websockets)
        raise NotImplementedError
    
    technologies_parsed = fetch_api(logger)

    """ 
    TODO
        * What do I return for production mode that are not even on the island ? 
            The main README says "The production values should never be negative. Use None, or omit the key if a specific production mode is not known." but doesn't answer this question
    """
    return {
      'countryCode': 'AUS-TAS-KI',
      'datetime': arrow.now(tz='Australia/Currie').datetime,
      'production': {
          'biomass': 0,
          'coal': 0,
          'gas': 0,
          'hydro': 0,
          'nuclear': 0,
          'oil': technologies_parsed['diesel'],
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
