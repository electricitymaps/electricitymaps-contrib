from datetime import datetime
from logging import Logger, getLogger

from requests import Session

from ..lib import IN, web, zonekey

ZONE_KEY = "IN-CT"
URL = "http://117.239.199.203/csptcl/GEN.aspx"
SOURCE = "cspc.co.in"
TIME_FORMAT = "hh:m DD-MM-YY"


def fetch_consumption(
    zone_key: str = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch Chhattisgarh consumption"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)

    india_date_time = IN.read_datetime_from_span_id(html, "L34", TIME_FORMAT)
    demand_value = IN.read_value_from_span_id(html, "L26")

    return {
        "zoneKey": zone_key,
        "datetime": india_date_time.datetime,
        "consumption": demand_value,
        "source": SOURCE,
    }


def fetch_production(
    zone_key: str = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch Chhattisgarh production"""

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)

    india_date_time = IN.read_datetime_from_span_id(html, "L34", "hh:m DD-MM-YY")
    korba_east_value = IN.read_value_from_span_id(html, "L3")
    korba_west_value = IN.read_value_from_span_id(html, "L9")
    dsmp_value = IN.read_value_from_span_id(html, "L12")
    marwa_value = IN.read_value_from_span_id(html, "L19")
    coal_value = round(
        korba_east_value + korba_west_value + dsmp_value + marwa_value, 2
    )
    bango_value = IN.read_value_from_span_id(html, "L16")

    return {
        "zoneKey": zone_key,
        "datetime": india_date_time.datetime,
        "production": {"coal": coal_value, "hydro": bango_value},
        "source": SOURCE,
    }


if __name__ == "__main__":
    session = Session()
    print(fetch_production(ZONE_KEY, session))
    print(fetch_consumption(ZONE_KEY, session))
