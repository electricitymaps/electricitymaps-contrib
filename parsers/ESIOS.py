#!/usr/bin/env python3

from os import environ
from urllib.parse import urlencode

# The arrow library is used to handle datetimes
import arrow

# The request library is used to fetch content through HTTP
import requests

from .lib.exceptions import ParserException
from .lib.utils import get_token


def fetch_exchange(
    zone_key1="ES", zone_key2="MA", session=None, target_datetime=None, logger=None
) -> list:

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    # Get ESIOS token
    token = get_token("ESIOS_TOKEN")

    ses = session or requests.Session()

    # Request headers
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json; application/vnd.esios-api-v2+json",
        "Authorization": 'Token token="{0}"'.format(token),
    }

    # Request query url
    utc = arrow.utcnow()
    start_date = utc.shift(hours=-24).floor("hour").isoformat()
    end_date = utc.ceil("hour").isoformat()
    dates = {"start_date": start_date, "end_date": end_date}
    query = urlencode(dates)
    url = "https://api.esios.ree.es/indicators/10209?{0}".format(query)

    response = ses.get(url, headers=headers)
    if response.status_code != 200 or not response.text:
        raise ParserException(
            "ESIOS", "Response code: {0}".format(response.status_code)
        )

    json = response.json()
    values = json["indicator"]["values"]
    if not values:
        raise ParserException("ESIOS", "No values received")
    else:
        data = []
        sorted_zone_keys = sorted([zone_key1, zone_key2])

        for value in values:
            # Get last value in datasource
            datetime = arrow.get(value["datetime_utc"]).datetime
            # Datasource negative value is exporting, positive value is importing
            net_flow = -value["value"]

            value_data = {
                "sortedZoneKeys": "->".join(sorted_zone_keys),
                "datetime": datetime,
                "netFlow": net_flow
                if zone_key1 == sorted_zone_keys[0]
                else -1 * net_flow,
                "source": "api.esios.ree.es",
            }

            data.append(value_data)

        return data


if __name__ == "__main__":
    session = requests.Session()
    print(fetch_exchange("ES", "MA", session))
