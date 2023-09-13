from datetime import datetime
from logging import Logger, getLogger

from requests import Session

from ..lib import IN, web, zonekey

URL = "https://core.ap.gov.in/CMDashBoard/UserInterface/Power/PowerReport.aspx"
ZONE_KEY = "IN-AP"
TIME_FORMAT = "DD-MM-YYYY HH:mm"
SOURCE = "core.ap.gov.in"


def fetch_production(
    zone_key: str = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch Andhra Pradesh  production"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)
    india_date = IN.read_datetime_from_span_id(
        html, "MainContent_lblPowerStatusDate", TIME_FORMAT
    )

    hydro_value = IN.read_value_from_span_id(html, "MainContent_lblHydel")
    gas_value = IN.read_value_from_span_id(html, "MainContent_lblGas")
    wind_value = IN.read_value_from_span_id(html, "MainContent_lblWind")
    solar_value = IN.read_value_from_span_id(html, "MainContent_lblSolar")

    # All thermal centrals are considered coal based production
    # https://en.wikipedia.org/wiki/Power_sector_of_Andhra_Pradesh
    thermal_value = IN.read_value_from_span_id(html, "MainContent_lblThermal")

    cgs_value = IN.read_value_from_span_id(html, "MainContent_lblCGS")
    ipp_value = IN.read_value_from_span_id(html, "MainContent_lblIPPS")

    return {
        "zoneKey": zone_key,
        "datetime": india_date.datetime,
        "production": {
            "biomass": 0.0,
            "coal": thermal_value,
            "gas": gas_value,
            "hydro": hydro_value,
            "nuclear": 0.0,
            "oil": 0.0,
            "solar": solar_value,
            "wind": wind_value,
            "geothermal": 0.0,
            "unknown": round(cgs_value + ipp_value, 2),
        },
        "storage": {"hydro": 0.0},
        "source": SOURCE,
    }


def fetch_consumption(
    zone_key: str = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Fetch Andhra Pradesh consumption"""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    zonekey.assert_zone_key(zone_key, ZONE_KEY)

    html = web.get_response_soup(zone_key, URL, session)
    india_date = IN.read_datetime_from_span_id(
        html, "MainContent_lblPowerStatusDate", TIME_FORMAT
    )

    demand_value = IN.read_value_from_span_id(html, "MainContent_lblGridDemand")

    return {
        "zoneKey": zone_key,
        "datetime": india_date.datetime,
        "consumption": demand_value,
        "source": SOURCE,
    }


if __name__ == "__main__":
    session = Session()
    print(fetch_production(ZONE_KEY, session))
    print(fetch_consumption(ZONE_KEY, session))
