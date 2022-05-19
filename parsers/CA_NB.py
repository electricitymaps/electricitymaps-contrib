#!/usr/bin/env python3

# The arrow library is used to handle datetimes consistently with other parsers
import arrow

# The request library is used to fetch content through HTTP
import requests

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup

timezone = "Canada/Atlantic"


def _get_new_brunswick_flows(requests_obj):
    """
    Gets current electricity flows in and out of New Brunswick.

    There is no reported data timestamp in the page.
    The page returns current time and says "Times at which values are sampled may vary by as much as 5 minutes."
    """

    url = "https://tso.nbpower.com/Public/en/SystemInformation_realtime.asp"
    response = requests_obj.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", attrs={"bordercolor": "#191970"})

    rows = table.find_all("tr")

    headers = rows[1].find_all("td")
    values = rows[2].find_all("td")

    flows = {
        headers[i].text.strip(): float(row.text.strip()) for i, row in enumerate(values)
    }

    return flows


def fetch_production(
    zone_key="CA-NB", session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known production mix (in MW) of a given country."""

    """
    In this case, we are calculating the amount of electricity generated
    in New Brunswick, versus imported and exported elsewhere.
    """

    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    requests_obj = session or requests.session()
    flows = _get_new_brunswick_flows(requests_obj)

    # nb_flows['NB Demand'] is the use of electricity in NB
    # 'EMEC', 'ISO-NE', 'MPS', 'NOVA SCOTIA', 'PEI', and 'QUEBEC'
    # are exchanges - positive for exports, negative for imports
    # Electricity generated in NB is then 'NB Demand' plus all the others

    generated = (
        flows["NB Demand"]
        + flows["EMEC"]
        + flows["ISO-NE"]
        + flows["MPS"]
        + flows["NOVA SCOTIA"]
        + flows["PEI"]
        + flows["QUEBEC"]
    )

    data = {
        "datetime": arrow.utcnow().floor("minute").datetime,
        "zoneKey": zone_key,
        "production": {"unknown": generated},
        "storage": {},
        "source": "tso.nbpower.com",
    }

    return data


def fetch_exchange(
    zone_key1, zone_key2, session=None, target_datetime=None, logger=None
) -> dict:
    """Requests the last known power exchange (in MW) between two regions."""
    if target_datetime:
        raise NotImplementedError("This parser is not yet able to parse past dates")

    sorted_zone_keys = "->".join(sorted([zone_key1, zone_key2]))

    requests_obj = session or requests.session()
    flows = _get_new_brunswick_flows(requests_obj)

    # In this source, positive values are exports and negative are imports.
    # In expected result, "net" represents an export.
    # So these can be used directly.

    if sorted_zone_keys == "CA-NB->CA-QC":
        value = flows["QUEBEC"]
    elif sorted_zone_keys == "CA-NB->US-NE-ISNE":
        # all of these exports are to Maine
        # (see https://www.nbpower.com/en/about-us/our-energy/system-map/),
        # currently this is mapped to ISO-NE
        value = flows["EMEC"] + flows["ISO-NE"] + flows["MPS"]
    elif sorted_zone_keys == "CA-NB->CA-NS":
        value = flows["NOVA SCOTIA"]
    elif sorted_zone_keys == "CA-NB->CA-PE":
        value = flows["PEI"]
    else:
        raise NotImplementedError("This exchange pair is not implemented")

    data = {
        "datetime": arrow.utcnow().floor("minute").datetime,
        "sortedZoneKeys": sorted_zone_keys,
        "netFlow": value,
        "source": "tso.nbpower.com",
    }

    return data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    print(fetch_production())

    print('fetch_exchange("CA-NB", "CA-PE") ->')
    print(fetch_exchange("CA-NB", "CA-PE"))
