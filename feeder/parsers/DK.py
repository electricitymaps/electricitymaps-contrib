import arrow
import requests
import xml.etree.ElementTree as ET

COUNTRY_CODE = 'DK'

def fetch_DK():
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

    obj = {
        'countryCode': COUNTRY_CODE,
        'datetime': arrow.get(arrow.get(data['Modified']).datetime, 
            'Europe/Copenhagen').datetime
    }
    obj['exchange'] = {
        'DE': float(data['Udveksling_JyllandTyskland']) + float(data['Udveksling_SjaellandTyskland']),
        'SE': float(data['Udveksling_JyllandSverige']) + float(data['Udveksling_BornholmSverige']) + + float(data['Udveksling_SjaellandSverige']),
        'NO': float(data['Udveksling_JyllandNorge'])
    }
    obj['consumption'] = {
        'unknown': float(data['Elforbrug'])
    }
    obj['production'] = {
        'nuclear': 0,
        'wind': float(data['Vindmoeller']),
        'solar': float(data['Solcelle_Produktion']),
        'unknown': float(data['Centrale_kraftvaerker']) + float(data['Decentrale_kraftvaerker']),
        'hydro': 0
    }

    return obj

if __name__ == '__main__':
    print fetch_DK()
