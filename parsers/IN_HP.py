#!/usr/bin/env python3

"""Parser for Himachal Pradesh (Indian State)."""

import datetime
import logging
from enum import Enum

import arrow
import requests
from bs4 import BeautifulSoup

# This URL is called from within the
# https://hpsldc.com/intra-state-power-transaction/
# page to load the data.
DATA_URL = "https://hpsldc.com/wp-admin/admin-ajax.php"
ZONE_KEY = "IN-HP"
TZ = "Asia/Kolkata"


class GenType(Enum):
    """
    Enum for plant generation types found in the data.
    Enum values are the keys for the production dictionary returned from fetch_production().
    """

    HYDRO = "hydro"
    UNKNOWN = "unknown"


# Map of plant names (as given in data source) to their type.
# Source for types is http://meritindia.in/state-data/himachal-pradesh
# (click 'Show details' at the bottom) or the link above/next to the
# relevant entry if there is no record in meritindia.
# Corroborating source: https://hpaldc.org/index.asp?pg=powStn
#
# Total plant capacity as manually calculated from the data source:
# GENERATION OF HP(Z): 992.45 MW Hydro, 608.26 MW Unknown.
# (Unknown capacity value not given in data, estimated as 135% of actual generation
# as this is the average ratio for plants with known capacity).
# (B1)ISGS(HPSLDC WEB PORTAL): 4483.02 MW Hydro.
# Total (for zones.json): 5475.47 MW Hydro, 608.26 MW Unknown.
PLANT_NAMES_TO_TYPES = {
    ### Plants in GENERATION OF HP(Z) table ###
    # Listed as ISGS in type source but state in data source
    "BASPA(3X100MW)": GenType.HYDRO,
    "BHABA(3X40MW)": GenType.HYDRO,
    "GIRI(2X30MW)": GenType.HYDRO,
    "LARJI(3X42MW)": GenType.HYDRO,
    "BASSI(4X16.5MW)": GenType.HYDRO,
    # http://globalenergyobservatory.org/geoid/44638
    "MALANA(2X43MW)": GenType.HYDRO,
    "ANDHRA(3X5.65MW)": GenType.HYDRO,
    "GHANVI(2X11.25MW)": GenType.HYDRO,  # GANVI in type source
    # https://www.ejatlas.org/conflict/kashang-hydroelectricity-project
    "KASHANG(3X65MW)": GenType.HYDRO,
    # https://cdm.unfccc.int/Projects/DB/RWTUV1354641854.75/view
    "Sawra Kuddu (3x37MW)": GenType.HYDRO,
    "MICROP/HMONITORED(HPSEBL)": GenType.UNKNOWN,  # No type source
    "IPPsP/HMONITORED": GenType.UNKNOWN,  # No type source
    "MICROP/HUNMONITORED": GenType.UNKNOWN,  # No type source
    ### Plants in (B1)ISGS(HPSLDC WEB PORTAL) table ###
    "BSIUL": GenType.HYDRO,  # BAIRASIUL HEP in type source.
    "CHAMERA1": GenType.HYDRO,
    "CHAMERA2": GenType.HYDRO,
    "CHAMERA3": GenType.HYDRO,
    "PARBATI3": GenType.HYDRO,
    "NJPC": GenType.HYDRO,  # NATHPA JHAKRI HEP in type source.
    "RAMPUR": GenType.HYDRO,
    "KOLDAM": GenType.HYDRO,
}


def fetch_production(
    zone_key=ZONE_KEY,
    session=None,
    target_datetime: datetime.datetime = None,
    logger: logging.Logger = logging.getLogger(__name__),
) -> dict:
    """Requests the last known production mix (in MW) of Himachal Pradesh (India)"""
    r = session or requests.session()
    if target_datetime is None:
        url = DATA_URL
    else:
        raise NotImplementedError("This parser is not yet able to parse past dates")
    res = r.post(url, {"action": "intra_state_power_transaction"})
    assert res.status_code == 200, (
        f"Exception when fetching production for "
        "{zone_key}: {res.status_code} error when calling url={url}"
    )
    soup = BeautifulSoup(res.text, "html.parser")
    return {
        "zoneKey": ZONE_KEY,
        "datetime": arrow.now(TZ).datetime,
        "production": combine_gen(
            get_state_gen(soup, logger), get_isgs_gen(soup, logger)
        ),
        "source": "hpsldc.com",
    }


def get_state_gen(soup, logger: logging.Logger):
    """
    Gets the total generation by type from state powerplants (MW).
    Data is from the table titled GENERATION OF HP(Z).
    """
    table_name = "GENERATION OF HP(Z)"
    gen = {GenType.HYDRO.value: 0.0, GenType.UNKNOWN.value: 0.0}
    # Read all rows except the last (Total).
    for row in get_table_rows(soup, "table_5", table_name)[:-1]:
        try:
            cols = row.find_all("td")
            # Column 1: plant name, column 2: current generation.
            gen_type = PLANT_NAMES_TO_TYPES[cols[0].text]
            gen[gen_type.value] += float(cols[1].text)
        except (AttributeError, KeyError, IndexError, ValueError):
            logger.error(
                f"Error importing data from row: {row}", extra={"key": ZONE_KEY}
            )
    return gen


def get_isgs_gen(soup, logger: logging.Logger):
    """
    Gets the total generation by type from ISGS powerplants (MW).
    ISGS means Inter-State Generating Station: one owned by multiple states.
    Data is from the table titled (B1)ISGS(HPSLDC WEB PORTAL).
    """
    table_name = "(B1)ISGS(HPSLDC WEB PORTAL)"
    gen = {GenType.HYDRO.value: 0.0, GenType.UNKNOWN.value: 0.0}
    # Read all rows except the first (headers) and last two (OTHERISGS and
    # Total).
    for row in get_table_rows(soup, "table_4", table_name)[1:-2]:
        try:
            cols = row.find_all("td")
            if not cols[0].has_attr("class"):
                # Ignore first column (COMPANY), which only has cells for some
                # rows (using rowspan).
                del cols[0]
            # Once COMPANY column is excluded, we have
            # column 1: plant name, column 3: current generation.
            gen_type = PLANT_NAMES_TO_TYPES[cols[0].text]
            gen[gen_type.value] += float(cols[2].text)
        except (AttributeError, KeyError, IndexError, ValueError):
            logger.error(
                f"Error importing data from row: {row}", extra={"key": ZONE_KEY}
            )
    return gen


def get_table_rows(soup, container_class, table_name):
    """Gets the table rows in the div identified by the provided class."""
    try:
        rows = soup.find("div", class_=container_class).find("tbody").find_all("tr")
        if len(rows) == 0:
            raise ValueError
        return rows
    except (AttributeError, ValueError) as err:
        raise Exception(f"Error reading table {table_name}: {err}")


def combine_gen(gen1, gen2):
    """
    Combines two dictionaries of generation data.

    Currently only does Hydro and Unknown as there are no other types in the
    data source.
    """
    return {
        GenType.HYDRO.value: round(
            gen1[GenType.HYDRO.value] + gen2[GenType.HYDRO.value], 2
        ),
        GenType.UNKNOWN.value: round(
            gen1[GenType.UNKNOWN.value] + gen2[GenType.UNKNOWN.value], 2
        ),
    }


def fetch_consumption(
    zone_key=ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    # Not currently implemented as this function is not used by the map,
    # but if required the data is available as 'Demand Met' on
    # https://hpsldc.com/
    raise NotImplementedError("Fetch production not implemented")


def fetch_price(
    zone_key=ZONE_KEY,
    session=None,
    target_datetime=None,
    logger=logging.getLogger(__name__),
):
    # The only price data available in the source is 'DSM Rate'.
    # I.e. Demand side management rate.
    # I believe (though I'm not sure) that this refers to a payment
    # made by the grid to consumers who reduce their consumption at times
    # of high demand, therefore it is not appropriate for this function.
    raise NotImplementedError("No price data available")


if __name__ == "__main__":
    print("fetch_production() ->")
    print(fetch_production())
