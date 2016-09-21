import arrow
import requests
import xml.etree.ElementTree as ET

COUNTRY_CODE = 'ES'

r = requests.session()

def fetch_ES():
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': '',
        'X-Requested-With': 'ShockwaveFlash/21.0.0.240',
        'Referer': 'https://demanda.ree.es/demandaGeneracionAreas.swf',
        'Origin': 'https://demanda.ree.es',
        'Host': 'demanda.ree.es',
        'Accept-Encoding': 'gzip, deflate'
    }
    # This api requires a timestamp-based key.
    # See http://mola.io/2013/08/29/unlocking-data-spain-power-generation/
    url = 'https://demanda.ree.es/WSVisionaV01/wsDemanda30FinoService?WSDL'
    body = """
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <SOAP-ENV:Body>
        <tns:consultaTiempo xmlns:tns="http://ws.wsDemanda24.ree.es/"/>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    """
    response = r.post(url, data=body, headers=headers)
    root = ET.fromstring(response.content)
    timestamp = root[0][0][0].text

    key = str(int(float(timestamp[5:10])/ 1.307000))
    url = 'https://demanda.ree.es/WSVisionaV01/wsDemanda30Service'
    body = """
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
      <SOAP-ENV:Body>
        <tns:demandaGeneracion30 xmlns:tns="http://ws.wsDemanda24.ree.es/">
          <fecha>%s</fecha>
          <clave>%s</clave>
        </tns:demandaGeneracion30>
      </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    """ % (arrow.now(tz='Europe/Madrid').format('YYYY-MM-DD'), key)

    response = r.post(url, data=body, headers=headers)
    root = ET.fromstring(response.content)
    data = None
    for data in root[0][0][0].getchildren(): pass

    parsed = {}
    for item in data.getchildren():
        parsed[item.tag] = item.text

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(arrow.get(parsed['timeStamp']).datetime, 
            'Europe/Madrid').datetime # We receive the time in local time
    }
    obj['consumption'] = {
        'unknown': float(parsed['demanda'])
    }
    obj['exchange'] = {
    }
    obj['production'] = {
        'gas': float(parsed['gasFuel']) + float(parsed['cicloComb']),
        'coal': float(parsed['carbon']),
        'solar': float(parsed['solar']), # = float(parsed['solTer']) + float(parsed['solFot']),
        'nuclear': float(parsed['nuclear']),
        'wind': float(parsed['eolica']),
        'hydro': float(parsed['hidro']),
        'unknown': float(parsed['termRenov']) + float(parsed['cogenResto']),
    }

    return obj

if __name__ == '__main__':
    print fetch_ES()
