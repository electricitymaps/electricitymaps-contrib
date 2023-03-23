#!/usr/bin/env python3

"""
Real-time parser for Puerto Rico.

Fetches data from various pages embedded as an iframe at https://aeepr.com/en-us/Pages/Generaci%C3%B3n.aspx

The electricity authority is known in English as PREPA (Puerto Rico Electric Power Authority) and in Spanish as AEEPR (Autoridad de Energía Eléctrica Puerto Rico)
"""

from datetime import datetime
from logging import Logger, getLogger
from typing import Optional

# The arrow library is used to handle datetimes
import arrow
from bs4 import BeautifulSoup
from requests import Session

timezone_name = "America/Puerto_Rico"

GENERATION_BREAKDOWN_URL = f"https://lumapr.com/system-overview/?lang=en"

# https://web.archive.org/web/20221210231416/https://aeepr.com/en-us/QuienesSomos/Pages/ElectricSystem.aspx
# "#6" appears to be a kind of heavy fuel oil, and "#2" a kind of diesel fuel
MAP_GENERATION_UNIT_NAME_TO_TYPE = {
    "San Juan": "oil",
    "Palo Seco": "oil",
    "Aguirre": "oil",
    "Costa Sur": "oil",  # Note: actually dual-fuel according to https://www.ccj-online.com/4q-2012/plant-report-ecoelectrica-lp/
    "Eco Eléctrica": "gas",  # https://ecoelectrica.net/sobre-nosotros/#laplanta
    "AES": "coal",  # https://web.archive.org/web/20230323203600/https://www.aespuertorico.com/sites/default/files/2022-10/CCR%20Annual%20Inspection%20Report%202022_Final_Sept%202022.pdf - note that the LUMA website mentions a max capacity of 550MW, and this document 520MW. Gross vs net or is it because of other (small) generation facilities?
    # Peaker plants
    "Mayaguez": "oil",  # https://energia.pr.gov/wp-content/uploads/sites/7/2022/05/Motion-to-Inform-Approval-of-Mayaguez-Project-NEPR-MI-2020-0012-1.pdf - note that the LUMA website mentions a max capacity of 250MW, and this document 220MW
    "Cambalache": "unknown",  # https://energia.pr.gov/wp-content/uploads/sites/7/2022/06/SL-015976.CA_Cambalache-IE-Report_Final.pdf - 247.5MW (3×82.5MW)
    "Gas Turbine": "unknown",  # In spite of the name, there are gas turbines that run on diesel; 'gas' doesn't mean 'natural gas' here
    "Aguirre Combined Cycle": "oil",
    # Renewables
    "Solar": "solar",
    "Wind": "wind",
    "Landfill Gas": "biomass",
    "Hydroelectric": "hydro",
}


def fetch_production(
    zone_key: str = "PR",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of a given region."""

    global renewable_output

    if target_datetime is not None and target_datetime < arrow.utcnow().shift(days=-1):
        raise NotImplementedError("The datasource currently only has data for today")

    r = session or Session()

    data = {  # To be returned as response data
        "zoneKey": zone_key,
        #'datetime': '2017-01-01T00:00:00Z',
        "production": {
            "biomass": 0.0,
            "coal": 0.0,
            "gas": 0.0,
            "hydro": 0.0,
            "nuclear": 0.0,
            "oil": 0.0,
            "solar": 0.0,
            "wind": 0.0,
            "geothermal": 0.0,
            "unknown": 0.0,
        },
        #   'storage': {
        #        'hydro': -10.0,
        #    },
        "source": "lumapr.com",
        "datetime": arrow.now(timezone_name).datetime,
    }

    res = r.get(
        GENERATION_BREAKDOWN_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0 ElectricityMaps.com",
        },
    )

    assert res.status_code == 200, (
        "Exception when fetching production for "
        "{}: error when calling url={}".format(zone_key, GENERATION_BREAKDOWN_URL)
    )

    # sourceData = extract_data(res.text)

    html = res.text
    soup = BeautifulSoup(html, "lxml")

    detailsContainer = soup.find("div", class_="container mt-5")

    # Make sure the heading is indeed "Power Supply in Details" (in case the page is re-arranged)
    detailsContainer_heading = detailsContainer.select("> h2")[0].string
    assert "Power Supply in Details" == detailsContainer_heading, (
        "Exception when extracting generation breakdown for {}: heading is not "
        "'Power Supply in Details' but is instead named {}".format(
            zone_key, thermal_production_breakdown_table_header
        )
    )

    generationGauges = detailsContainer.select(".gauge-container")

    for generationGauge in generationGauges:
        unit_name = generationGauge.select("> .label-container > .label")[0].string
        unit_generation = float(generationGauge["data-value"])

        if unit_name in MAP_GENERATION_UNIT_NAME_TO_TYPE:
            if unit_generation > 0:  # Ignore self-consumption
                unit_type = MAP_GENERATION_UNIT_NAME_TO_TYPE[unit_name]
                data["production"][unit_type] += unit_generation
        else:
            logger.warning(
                extra={"key": zone_key},
            )

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""
    print("fetch_production() ->")
    print(fetch_production())
# TODO add forecast parser
#    print('fetch_generation_forecast() ->')
#    print(fetch_generation_forecast())
