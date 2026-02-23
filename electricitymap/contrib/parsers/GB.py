"""Parser that uses the RTE-FRANCE API"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import (
    PriceList,
    ProductionBreakdownList,
)
from electricitymap.contrib.lib.models.events import (
    EventSourceType,
    ProductionMix,
    StorageMix,
)
from electricitymap.contrib.parsers.GB_battery_units import BATTERY_UNITS
from electricitymap.contrib.parsers.lib.config import refetch_frequency
from electricitymap.contrib.parsers.lib.exceptions import ParserException
from electricitymap.contrib.types import ZoneKey

PARSER = "GB.py"
TIMEZONE = ZoneInfo("Europe/London")
ZONE_KEY = ZoneKey("GB")

NESO_API = "https://api.neso.energy/api/3/action/datastore_search_sql"
NESO_GENERATION_DATASET_ID = "f93d1835-75bc-43e5-84ad-12472b180a98"

ELEXON_BMU_UNITS = "https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all"
ELEXON_BMU_VALUES = "https://data.elexon.co.uk/bmrs/api/v1/balancing/physical/all"


NESO_TO_PRODUCTION_MIX_MAPPING = {
    "BIOMASS": "biomass",
    "COAL": "coal",
    "GAS": "gas",
    "HYDRO": "hydro",
    "NUCLEAR": "nuclear",
    "SOLAR": "solar",
    "WIND": "wind",
    "WIND_EMB": "wind",
    "OTHER": "unknown",
}


@refetch_frequency(timedelta(days=2))
def fetch_price(
    zone_key: ZoneKey = ZONE_KEY,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    """Requests the power price per MWh of a given country.

    This function will return one-hourly prices for the requested day, and previous one. For live data, it will also
    return prices from day-ahead market data.
    """

    now = datetime.now(timezone.utc)
    target_datetime = (
        now if target_datetime is None else target_datetime.astimezone(timezone.utc)
    )
    is_today = target_datetime.date() == now.date()

    # API works in UTC timestamps, and allows fetching day-ahead market data
    num_backlog_days = 1
    day_start = (target_datetime - timedelta(days=num_backlog_days)).strftime(
        "%d/%m/%Y"
    )
    day_end = (target_datetime + timedelta(days=1 if is_today else 0)).strftime(
        "%d/%m/%Y"
    )
    url = f"http://eco2mix.rte-france.com/curves/getDonneesMarche?dateDeb={day_start}&dateFin={day_end}&mode=NORM"

    session = session or Session()
    response = session.get(url)

    if not response.ok:
        raise ParserException(
            PARSER,
            f"Exception when fetching price error code: {response.status_code}: {response.text}",
            zone_key,
        )

    xml_tree = ET.fromstring(response.content)

    price_list = PriceList(logger=logger)
    for daily_market_data in xml_tree.iterfind("donneesMarche"):
        date = daily_market_data.get("date")
        if date is None:
            raise ParserException(
                PARSER,
                "Exception when parsing price API response: missing 'date' for daily market data.",
                zone_key,
            )
        day = datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        for daily_zone_data in daily_market_data:
            zone_code = daily_zone_data.get("perimetre")

            # Data for Germany / Luxembourg is not set / reported as aggregate region
            if zone_code in {"DE", "DL"}:
                continue

            if zone_key != zone_code:
                continue

            granularity = daily_zone_data.get("granularite")
            if granularity != "Global":
                continue

            for value in daily_zone_data:
                price = (
                    None
                    if value.text == "ND"
                    else float(value.text)
                    if value.text is not None
                    else None
                )
                if price is None:
                    continue

                period_number = int(value.attrib["periode"])
                dt = day + timedelta(hours=period_number)

                price_list.append(
                    zoneKey=zone_key,
                    datetime=dt,
                    source="rte-france.com",
                    price=price,
                    currency="EUR",
                    # Can use EventSourceType.measured even for dt > now entries as price is set on day-ahead market
                    sourceType=EventSourceType.measured,
                )

    return price_list.to_list()


def fetch_production(
    zone_key: ZoneKey,
    session: Session | None = None,
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    session = session or Session()

    if target_datetime is None:
        start_datetime = datetime.now(tz=ZoneInfo("UTC")) - timedelta(hours=24)
        sql_query = f"""SELECT * FROM "{NESO_GENERATION_DATASET_ID}" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""

    elif target_datetime > datetime(year=2009, month=1, day=1):
        target_datetime = target_datetime.astimezone(ZoneInfo("Europe/London"))
        start_datetime = target_datetime - timedelta(hours=2)
        end_datetime = target_datetime + timedelta(hours=2)

        sql_query = f"""SELECT * FROM "{NESO_GENERATION_DATASET_ID}" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' AND "DATETIME" <= '{end_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""
    else:
        raise ParserException(
            "GB.py",
            "This parser is not yet able to parse dates before 2009-01-01",
            zone_key,
        )

    params = {"sql": sql_query}

    res: Response = session.get(NESO_API, params=params)
    if not res.status_code == 200:
        raise ParserException(
            "GB.py",
            f"Exception when fetching production error code: {res.status_code}: {res.text}",
            zone_key,
        )

    obj = res.json()["result"]["records"]

    hydro_units = get_hydro_storage_units(session, zone_key)

    production_list = ProductionBreakdownList(logger=logger)
    for row in obj:
        production_mix = ProductionMix()

        for neso_key, emaps_key in NESO_TO_PRODUCTION_MIX_MAPPING.items():
            production_mix.add_value(emaps_key, float(row[neso_key]))

        timestamp = datetime.fromisoformat(row["DATETIME"]).replace(
            tzinfo=ZoneInfo("UTC")
        )

        storage_mix = fetch_storage(zone_key, session, timestamp, hydro_units)

        production_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=production_mix,
            storage=storage_mix,
            source="neso.energy, elexon",
        )

    return production_list.to_list()


def fetch_storage_for_units(units, timestamp: datetime, session: Session):
    storage = 0
    settlement_period = 1 + (timestamp.hour * 2) + (timestamp.minute // 30)
    params = {
        "dataset": "PN",
        "settlementDate": timestamp.strftime("%Y-%m-%d"),
        "settlementPeriod": settlement_period,
        "bmUnit": units,
    }

    res = session.get(ELEXON_BMU_VALUES, params=params)
    if not res.status_code == 200:
        raise ParserException(
            "GB.py",
            f"Exception when fetching storage units error code: {res.status_code}: {res.text}",
            zone_key,
        )

    for r in res.json()["data"]:
        timefrom = datetime.strptime(r["timeFrom"], "%Y-%m-%dT%H:%M:%SZ")
        timeto = datetime.strptime(r["timeTo"], "%Y-%m-%dT%H:%M:%SZ")
        minutes = (timeto - timefrom).total_seconds() / 60

        produced = (
            float(r["levelFrom"]) * minutes / 30
        )  # average power over the half hour
        storage += produced

    return storage


def fetch_storage(
    zone_key: ZoneKey,
    session: Session,
    timestamp: datetime,
    hydro_units: list[str],
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    storage_mix = StorageMix()
    # Hydro storage
    hydro_storage = fetch_storage_for_units(hydro_units, timestamp, session)
    storage_mix.add_value("hydro", -hydro_storage)
    # Battery storage
    battery_storage = fetch_storage_for_units(BATTERY_UNITS, timestamp, session)
    storage_mix.add_value("battery", -battery_storage)
    return storage_mix


def get_hydro_storage_units(session: Session, zone_key: ZoneKey) -> list[str]:
    res = session.get(ELEXON_BMU_UNITS)
    if not res.status_code == 200:
        raise ParserException(
            "GB.py",
            f"Exception when fetching storage units error code: {res.status_code}: {res.text}",
            zone_key,
        )

    hydro_storage_units = []
    for r in res.json():
        if r["fuelType"] == "PS":  # PS = pumped storage
            hydro_storage_units.append(r["elexonBmUnit"])

    return hydro_storage_units


if __name__ == "__main__":
    for zone_key in ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]:
        print(f"fetch_price({zone_key}) ->")
        print(fetch_price(ZoneKey(zone_key)))

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    print(f"fetch_price(target_datetime={historical_datetime.isoformat()}) ->")
    print(fetch_price(target_datetime=historical_datetime))
