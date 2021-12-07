from __future__ import annotations

import arrow
import requests

from parsers.lib.exceptions import ParserException

CONSUMPTION_URL = 'https://www.saskpower.com/ignitionapi/Content/GetNetLoad'
SOURCE = 'saskpower.com'
ZONE_KEY = 'CA-SK'


def fetch_consumption(zone_key=ZONE_KEY, session=None, target_datetime=None, logger=None):
    if target_datetime:
        raise NotImplementedError('This parser is not yet able to parse past dates')

    request = session or requests.session()
    response = request.get(url=CONSUMPTION_URL)
    if response.ok:
        decoded_content = response.content.decode(response.encoding)
        consumption = float(decoded_content.strip('"'))
        date_header = response.headers.get('date')
        consumption_date = arrow.get(date_header, 'ddd, DD MMM YYYY HH:mm:ss ZZZ').datetime

        return {
            'zoneKey': zone_key,
            'datetime': consumption_date,
            'consumption': consumption,
            'source': SOURCE
        }
    else:
        raise ParserException('CA_SK.py', 'HTTP request for current consumption failed', zone_key)


if __name__ == '__main__':
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print('fetch_consumption() ->')
    print(fetch_consumption())
