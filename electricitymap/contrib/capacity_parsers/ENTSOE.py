from datetime import datetime
from logging import getLogger

from bs4 import BeautifulSoup
from requests import Session

from electricitymap.contrib.config import ZoneKey
from parsers.ENTSOE import ENTSOE_DOMAIN_MAPPINGS, query_ENTSOE

"""
Update capacity configurations for ENTOS-E zones for a chosen year.
"""
logger = getLogger(__name__)
SOURCE = "entsoe.eu"

ENDPOINT = "/api"
ENTSOE_HOST = "https://web-api.tp.entsoe.eu"


EU_PROXY = "https://eu-proxy-jfnx5klx2a-ew.a.run.app{endpoint}?host={host}"

ENTSOE_ENDPOINT = ENTSOE_HOST + ENDPOINT
ENTSOE_EU_PROXY_ENDPOINT = EU_PROXY.format(endpoint=ENDPOINT, host=ENTSOE_HOST)


ENTSOE_ZONES = [
    "AL",
    "AT",
    "BA",
    "BE",
    "BG",
    "CZ",
    "DE",
    "DK-DK1",
    "DK-DK2",
    "EE",
    "ES",
    "FI",
    "FR",
    "GR",
    "HR",
    "HU",
    "IE",
    "LT",
    "LU",
    "LV",
    "ME",
    "MK",
    "NL",
    "NO-NO1",
    "NO-NO2",
    "NO-NO3",
    "NO-NO4",
    "NO-NO5",
    "PL",
    "PT",
    "RO",
    "SI",
    "SK",
    "RS",
    "XK",
    "UA",
]
ENTSOE_PARAMETER_TO_MODE = {
    "B01": "biomass",
    "B02": "coal",
    "B03": "coal",
    "B04": "gas",
    "B05": "coal",
    "B06": "oil",
    "B07": "coal",
    "B08": "coal",
    "B09": "geothermal",
    "B10": "hydro storage",
    "B11": "hydro",
    "B12": "hydro",
    "B13": "unknown",
    "B14": "nuclear",
    "B15": "unknown",
    "B16": "solar",
    "B17": "biomass",
    "B18": "wind",
    "B19": "wind",
    "B20": "unknown",
}


def query_capacity(
    in_domain: str, session: Session, target_datetime: datetime
) -> str | None:
    params = {
        "documentType": "A68",
        "processType": "A33",
        "in_Domain": in_domain,
        "periodStart": target_datetime.strftime("%Y01010000"),
        "periodEnd": target_datetime.strftime("%Y12312300"),
    }
    return query_ENTSOE(
        session,
        params,
        target_datetime=target_datetime,
        function_name=query_capacity.__name__,
    )


def fetch_production_capacity(zone_key: ZoneKey, target_datetime: datetime) -> dict:
    xml_str = query_capacity(
        ENTSOE_DOMAIN_MAPPINGS[zone_key], Session(), target_datetime
    )
    soup = BeautifulSoup(xml_str, "html.parser")
    # Each timeserie is dedicated to a different fuel type.
    capacity_dict = {}
    for timeseries in soup.find_all("timeseries"):
        fuel_code = str(
            timeseries.find_all("mktpsrtype")[0].find_all("psrtype")[0].contents[0]
        )
        end_date = datetime.strptime(
            timeseries.find_all("end")[0].contents[0], "%Y-%m-%dT%H:00Z"
        )
        if end_date.year != target_datetime.year:
            pass  # query_ENTSOE fetches data for 2 years, so we need to filter out the data for the previous year
        else:
            point = timeseries.find_all("point")
            value = float(point[0].find_all("quantity")[0].contents[0])
            if ENTSOE_PARAMETER_TO_MODE[fuel_code] in capacity_dict:
                capacity_dict[ENTSOE_PARAMETER_TO_MODE[fuel_code]]["value"] += value
            else:
                fuel_capacity_dict = {}
                fuel_capacity_dict["value"] = value
                fuel_capacity_dict["datetime"] = end_date.strftime("%Y-01-01")
                fuel_capacity_dict["source"] = SOURCE
                capacity_dict[ENTSOE_PARAMETER_TO_MODE[fuel_code]] = fuel_capacity_dict
    if capacity_dict:
        print(
            f"ENTSO-E capacity parser found capacity data for {zone_key} on {target_datetime.date()}: \n{capacity_dict}"
        )
        return capacity_dict
    else:
        logger.warning(
            f"ENTSO-E capacity parser failed to find capacity data for {zone_key} on {target_datetime.date()}"
        )


def fetch_production_capacity_for_all_zones(target_datetime: datetime) -> dict:
    capacity_dict = {}
    for zone in ENTSOE_ZONES:
        try:
            zone_capacity = fetch_production_capacity(zone, target_datetime)
            capacity_dict[zone] = zone_capacity
            print(
                f"Fetched capacity for {zone} on {target_datetime.date()}: {zone_capacity}"
            )
        except:
            print(f"Failed to update capacity for {zone} on {target_datetime.date()}")
            continue
    return capacity_dict