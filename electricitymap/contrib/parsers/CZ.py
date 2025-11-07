from datetime import datetime, timedelta
from logging import Logger, getLogger

from bs4 import BeautifulSoup

# The request library is used to fetch content through HTTP
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    ExchangeList,
    ProductionBreakdownList,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.lib.types import ZoneKey
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException

# please try to write PEP8 compliant code (use a linter). One of PEP8's
# requirement is to limit your line length to 79 characters.

translate_table_gen = {
    "TPP": "coal",  # coal
    "CCGT": "gas",  # gas and steem gas
    "NPP": "nuclear",  # Nuclear
    "HPP": "hydro",  # Water
    "PsPP": "hydro",  # Pump Water storage
    "AltPP": "biomass",  # Alternative
    "ApPP": "unknown",  # factory
    "PVPP": "solar",  # photovoltaic
    "WPP": "wind",  # wind
    "unknown": "unknown",
}
translate_table_dist = {
    "SEPS": "SK",
    "APG": "AT",
    "PSE": "PL",
    "TenneT": "DE",
    "50HzT": "DE",
}

url = "https://www.ceps.cz/_layouts/CepsData.asmx"
source = "ceps.cz"


def get_mapper(xmlload):
    series = xmlload.find("series")
    mapping = {}
    for tag in series:
        generator = tag["name"].replace(" [MW]", "")
        mapping[generator] = tag["id"]

    return mapping


def make_request(session, payload, zone_key):
    headers = {
        "Content-Type": "application/soap+xml; charset=utf-8",
        "Content-Length": "1",
    }

    res: Response = session.post(url, headers=headers, data=payload)
    assert res.status_code == 200, (
        f"Exception when fetching production for {zone_key}: error when calling {url}"
    )

    return res


def get_target_datetime(dt: datetime | None) -> datetime:
    if dt is None:
        now = datetime.now()
        dt = (now - timedelta(minutes=now.minute % 15)).replace(second=0, microsecond=0)
    return dt


def __get_exchange_data(
    zone_key1: ZoneKey = ZoneKey("CZ"),
    zone_key2: ZoneKey = ZoneKey("DE"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
    mode: str = "Actual",
) -> list:
    target_datetime = get_target_datetime(target_datetime)
    from_datetime = target_datetime - timedelta(hours=48)

    payload = """<?xml version="1.0" encoding="utf-8"?>
    <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
      <soap12:Body>
        <CrossborderPowerFlows xmlns="https://www.ceps.cz/CepsData/">
          <dateFrom>{}</dateFrom>
          <dateTo>{}</dateTo>
          <agregation>{}</agregation>
          <function>{}</function>
          <version>{}</version>
        </CrossborderPowerFlows>
      </soap12:Body>
    </soap12:Envelope>""".format(
        from_datetime.isoformat(), target_datetime.isoformat(), "QH", "AVG", "RT"
    )

    content = make_request(session, payload, zone_key1).text
    xml = BeautifulSoup(content, "xml")
    mapper = get_mapper(xml)
    data_tag = xml.find("data")
    exchanges = ExchangeList(logger)

    if data_tag is not None:
        for values in data_tag:
            totalNetFlow = 0.0

            for k, v in mapper.items():
                country = "".join(
                    [
                        c
                        for key, c in translate_table_dist.items()
                        if key in k and mode in k
                    ]
                )
                if country != "" and country in (zone_key1, zone_key2):
                    netFlow = float(values[v])
                    totalNetFlow += -1 * netFlow if zone_key1 == "CZ" else netFlow

            exchanges.append(
                zoneKey=ZoneKey(f"{zone_key1}->{zone_key2}"),
                datetime=datetime.fromisoformat(values["date"]),
                source=source,
                netFlow=totalNetFlow,
            )

    else:
        zone_key = f"{zone_key1}->{zone_key2}"
        raise ParserException(
            "CZ.py",
            f"There was no data returned for {zone_key1} and {zone_key2} at {target_datetime}",
            zone_key,
        )

    return exchanges.to_list()


@refetch_frequency(timedelta(days=2))
def fetch_production(
    zone_key: ZoneKey = ZoneKey("CZ"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list:
    target_datetime = get_target_datetime(target_datetime)
    from_datetime = target_datetime - timedelta(hours=48)

    payload = """<?xml version="1.0" encoding="utf-8"?>
            <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
              <soap12:Body>
                <Generation xmlns="https://www.ceps.cz/CepsData/">
                  <dateFrom>{}</dateFrom>
                  <dateTo>{}</dateTo>
                  <agregation>{}</agregation>
                  <function>{}</function>
                  <version>{}</version>
                  <para1>{}</para1>
                </Generation>
              </soap12:Body>
            </soap12:Envelope>""".format(
        from_datetime.isoformat(), target_datetime.isoformat(), "QH", "AVG", "RT", "all"
    )

    content = make_request(session, payload, zone_key).text
    xml = BeautifulSoup(content, "xml")
    mapper = get_mapper(xml)

    data_tag = xml.find("data")
    production_breakdowns = ProductionBreakdownList(logger)

    if data_tag is not None:
        for values in data_tag:
            production = ProductionMix()
            storage = StorageMix()

            for k, v in mapper.items():
                generator = translate_table_gen[k]
                if k != "PsPP":
                    production.add_value(mode=generator, value=float(values[v]))
                else:
                    storage.add_value(mode=generator, value=float(values[v]) * -1)

            production_breakdowns.append(
                zoneKey=zone_key,
                datetime=datetime.fromisoformat(values["date"]),
                source=source,
                production=production,
                storage=storage,
            )

    else:
        ParserException(
            "CZ.py",
            f"There was no data returned for {zone_key} at {target_datetime}",
            zone_key,
        )

    return production_breakdowns.to_list()


@refetch_frequency(timedelta(days=1))
def fetch_exchange(
    zone_key1: ZoneKey = ZoneKey("CZ"),
    zone_key2: ZoneKey = ZoneKey("DE"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    return __get_exchange_data(
        zone_key1, zone_key2, session, target_datetime, logger, mode="Actual"
    )


def fetch_exchange_forecast(
    zone_key1: ZoneKey = ZoneKey("CZ"),
    zone_key2: ZoneKey = ZoneKey("DE"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    return __get_exchange_data(
        zone_key1, zone_key2, session, target_datetime, logger, mode="Planned"
    )


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    # print("fetch_production() ->")
    # print(fetch_production())
    # print("fetch_price() ->")
    # print(fetch_price())
    # print("fetch_exchange_forecast('AT', 'CZ') ->")
    # print(fetch_exchange_forecast("AT", "CZ"))
    print("fetch_exchange('AT', 'CZ') ->")
    print(fetch_exchange(ZoneKey("AT"), ZoneKey("CZ")))
