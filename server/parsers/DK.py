import arrow
import requests
import xml.etree.ElementTree as ET

def fetch_dk():
    url = 'http://energinet.dk/_layouts/FlashProxy.asmx'
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'http://energinet.dk/FlashProxy/GetSharePointListXML'
    }
    body = """<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
      <GetSharePointListXML xmlns="http://energinet.dk/FlashProxy">
        <sSiteUrl>http://energinet.dk/</sSiteUrl>
        <sListGUID>92446C99-A9CC-438E-BA20-12A38BEF2273</sListGUID>
        <sViewGUID/>
        <sFieldsList/>
        <sQuery/>
      </GetSharePointListXML>
    </soap:Body>
    </soap:Envelope>"""

    response = requests.post(url, data=body, headers=headers)
    root = ET.fromstring(response.content)
    data = root[0][0][0][0][0][0].attrib

    return {
        'datetime': arrow.get(arrow.get(data['Modified']).datetime, 
            'Europe/Copenhagen').datetime,
        'co2': float(data['_x0043_O2']),
        'consumption': float(data['Elforbrug']),
        'windProduction': float(data['Vindmoeller']),
        'solarProduction': float(data['Solcelle_Produktion'])
        #'central': float(data['Centrale_kraftvaerker']),
        #'local_chp': float(data['Decentrale_kraftvaerker']),
        #'import': float(data['Udveksling'])
    }
