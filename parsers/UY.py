#!/usr/bin/python3
import re
from datetime import datetime, timedelta
from logging import Logger, getLogger
from typing import Optional

import arrow
import dateutil

# BeautifulSoup is used to parse HTML to get information
from bs4 import BeautifulSoup
from requests import Session

tz = "America/Montevideo"

# maps the xml keys from the website to names used by parser system
MAP_GENERATION = {
    # short for rio negro, main hydro power plant
    "hydro": "r",
    "wind": "eolica",
    "solar": "fotovoltaica",
    "biomass": "biomasa",
    # all thermal, i.e. miscilaneous oil + natural gas production
    "unknown": "termica",
    "trade": "intercambios",
    "demand": "demanda",
    "salto_grande_prod": "comprassgu",
}

AVALIABLE_KEYS = ["hydro", "wind", "solar", "biomass", "unknown"]

UTE_URL = url = "https://ute.com.uy/energia-generada-intercambios-demanda"

SALTO_GRANDE_URL = "http://www.cammesa.com/uflujpot.nsf/FlujoW?OpenAgent&Tensiones y Flujos de Potencia&"


def get_salto_grande(session: Session, targ_time: Optional[datetime] = None) -> float:
    """Finds the current generation from the Salto Grande Dam that is allocated to Uruguay."""
    # handle optional arguments
    s = session or Session()
    lookup_time = datetime.now(tz=tz) if targ_time is None else targ_time

    # Data for current hour seems to be available after 30mins.
    # if we're too soon into the hour, check the hour before
    current_time = arrow.now("UTC-3")
    if (
        current_time.floor("hour") == targ_time.floor("hour")
        and current_time.minute < 30
    ):
        print(
            "Looking at previous hour's data for salto grande, because it is too soon after the hour"
        )
        current_time = current_time.shift(hours=-1)

    lookup_time: str = lookup_time.floor("hour").format("DD/MM/YYYY HH:mm")

    url = SALTO_GRANDE_URL + lookup_time
    response = s.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tie = soup.find("div", style="position:absolute; top:143; left:597")
    generation = float(tie.text)

    return generation


def parse_num(num_str: str) -> float:
    """
    given a string containing a decimal number in
    south american format, e.g. '23.456,45' using ',' as a decimal
    and '.' as a separator, convert to the corresponding float
    :param num_str: string containing a number south american format,
        e.g. '23.456,45' using ',' as a decimal
    :returns: a float with the value denoted by num_str
    """
    return float(num_str.strip().replace(".", "").replace(",", "."))


def correct_for_salto_grande(entry, session: Session):
    """
    corrects a single entry parsed from the UTE website using salto_grande data
    Switched this to only operate on a single entry or list of entries so
    fewer requests are needed
    """
    # https://github.com/tmrowco/electricitymap/issues/1325#issuecomment-380453296
    salto_grande = get_salto_grande(session, entry["time"])
    entry["hydro"] = entry["hydro"] + salto_grande
    return entry


# time:
def parse_page(session: Session):
    """
    Queries the url in UTE_URL, and parses hourly production and trade data
    and retruns the results as a list of dictionary objects
    """
    # load page
    resp = session.get(UTE_URL)

    # get the encoded XML with all the data we want
    soup = BeautifulSoup(resp.text, "html.parser")
    xml_tag = soup.find(id="valoresParaGraficar")
    xml_string = f"<{xml_tag.contents[0]}>{xml_tag.contents[1]}"

    # Use beautiful soup  to actually parse that XML string, and get information
    xml_doc = BeautifulSoup(xml_string, "lxml")

    # Data is encoded hourly... get that subsection of the document
    # then get the data for each encoded hour, as a json-like object
    hourly = xml_doc.find("fuentesporhora")
    hour_recs = []
    for hour in hourly.find_all("nodo"):
        # get generation data
        datum = {
            key: parse_num(hour.find(spanish).contents[0])
            for key, spanish in MAP_GENERATION.items()
        }
        # solar can sometimes return -0.1 at night, round up to 0
        datum["solar"] = max(datum["solar"], 0)

        # ingest date field
        datefield = hour.find("hora").contents[0]
        datestr = re.findall("\d\d/\d\d/\d\d\d\d \d+:\d\d", str(datefield))[0]
        date = arrow.get(datestr, "DD/MM/YYYY h:mm").replace(
            tzinfo=dateutil.tz.gettz(tz)
        )
        datum["time"] = date

        # add to list
        hour_recs.append(datum)
    return hour_recs


def get_entry_for_time(
    session: Optional[Session] = None, target_datetime: Optional[datetime] = None
) -> dict:
    """
    If possible, fetches the data entry from the given time
    Handles optional session and datetime logic.

    If datetime is specified, the function will first fetch data for all avaliable times, then
    return the data for the appropriate hour if possible

    Throws NotImplementedError if the time input is outside the acceptable range.
    """
    # handle optional argument
    session = Session() if session is None else session

    # get data from webpage
    entries = parse_page(session)

    # if using timestamp lookup, get the appropriate
    if target_datetime:
        targ = arrow.Arrow.fromdatetime(target_datetime)
        entry = None
        for candidate_entry in entries:
            if candidate_entry["time"].floor("hour") == targ.floor("hour"):
                entry = candidate_entry
        if entry is None:
            raise NotImplementedError(
                "This parser is not yet able to parse dates more than a day in the past"
            )
    else:
        entry = entries[-1]
    # https://github.com/tmrowco/electricitymap/issues/1325#issuecomment-380453296
    entry = correct_for_salto_grande(entry, session)
    return entry


def fetch_consumption(
    zone_key: str = "UY",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:

    # handle all session and time logics in get_entry_for_time function
    entry = get_entry_for_time(session, target_datetime)

    data = {
        "zoneKey": zone_key,
        "datetime": entry["time"].datetime,
        "consumption": entry["demand"],
        "source": "ute.com.uy",
    }

    return data


def fetch_production(
    zone_key: str = "UY",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:

    # handle all session and time logics in get_entry_for_time function
    entry = get_entry_for_time(session, target_datetime)

    data = {
        "zoneKey": zone_key,
        "datetime": entry["time"].datetime,
        "production": {key: entry[key] for key in AVALIABLE_KEYS},
        "source": "ute.com.uy",
    }

    return data


def fetch_exchange(
    zone_key1: str = "UY",
    zone_key2: str = "BR-S",
    session: Optional[Session] = None,
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> dict:
    """Requests the last known power exchange (in MW) between two countries."""

    # set comparison
    if {zone_key1, zone_key2} != {"UY", "BR"}:
        return None

    # handle all session and time logics in get_entry_for_time function
    entry = get_entry_for_time(session, target_datetime)

    netFlow = entry["trade"]  # this represents BR->UY (imports)
    if zone_key1 != "BR":
        netFlow *= -1

    data = {
        "sortedZoneKeys": "->".join(sorted([zone_key1, zone_key2])),
        "datetime": entry["time"].datetime,
        "netFlow": netFlow,
        "source": "ute.com.uy",
    }

    return data


if __name__ == "__main__":
    print("fetch_production(hour -1 ) ->")
    print(fetch_production(target_datetime=datetime.now() - timedelta(hours=1)))
    print("fetch_production() ->")
    print(fetch_production())
    print("fetch_consumption() ->")
    print(fetch_consumption())
    print("fetch_exchange(UY, BR) ->")
    print(fetch_exchange("UY", "BR"))
