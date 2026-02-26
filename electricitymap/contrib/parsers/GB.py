"""Parser that uses the RTE-FRANCE API"""

import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from io import BytesIO
from logging import Logger, getLogger
from zoneinfo import ZoneInfo

from openpyxl import load_workbook
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
ELEXON_BOALF_STREAM = "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOALF/stream"
ELEXON_BMU_FUEL_TYPE_URL = (
    "https://www.elexon.co.uk/documents/data/operational-data/bmu-fuel-type/"
)


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
        start_datetime = datetime.now(tz=ZoneInfo("UTC")) - timedelta(hours=12)
        sql_query = f"""SELECT * FROM "{NESO_GENERATION_DATASET_ID}" WHERE "DATETIME" >= '{start_datetime.strftime("%Y-%m-%d")}' ORDER BY "DATETIME" ASC"""

    elif target_datetime > datetime(year=2009, month=1, day=1):
        target_datetime = target_datetime.astimezone(ZoneInfo("Europe/London"))
        start_datetime = target_datetime - timedelta(hours=6)
        end_datetime = target_datetime + timedelta(hours=6)

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
    battery_units = get_battery_units(session, zone_key)

    production_list = ProductionBreakdownList(logger=logger)
    for row in obj:
        production_mix = ProductionMix()

        for neso_key, emaps_key in NESO_TO_PRODUCTION_MIX_MAPPING.items():
            production_mix.add_value(emaps_key, float(row[neso_key]))

        timestamp = datetime.fromisoformat(row["DATETIME"]).replace(
            tzinfo=ZoneInfo("UTC")
        )

        storage_mix = fetch_storage(session, timestamp, hydro_units, battery_units)

        production_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=production_mix,
            storage=storage_mix,
            source="neso.energy, elexon",
        )

    return production_list.to_list()


def _extract_data_rows(payload: dict | list) -> list[dict]:
    if isinstance(payload, dict):
        data = payload.get("data")
        return data if isinstance(data, list) else []
    return payload if isinstance(payload, list) else []


def _to_float(value: float | int | str | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, float | int):
        return float(value)
    if isinstance(value, str):
        stripped = value.strip()
        if stripped == "":
            return None
        return float(stripped)


def _extract_dataset_value(record: dict) -> tuple[bool, float | None]:
    value_keys = ["levelFrom", "quantity", "value", "boalf"]
    for key in value_keys:
        if key in record:
            return True, _to_float(record.get(key))
    return False, None


def _extract_storage_key(record: dict) -> tuple[str, str, str] | None:
    unit = record.get("bmUnit") or record.get("elexonBmUnit") or "__all_units__"
    time_from = record.get("timeFrom") or record.get("startTime") or ""
    time_to = record.get("timeTo") or record.get("endTime") or ""
    return str(unit), str(time_from), str(time_to)


def _interval_minutes(interval_key: tuple[str, str, str]) -> float:
    _, time_from, time_to = interval_key
    if time_from and time_to:
        start = datetime.strptime(time_from, "%Y-%m-%dT%H:%M:%SZ")
        end = datetime.strptime(time_to, "%Y-%m-%dT%H:%M:%SZ")
        return (end - start).total_seconds() / 60
    return 30


def _fetch_storage_dataset(
    session: Session,
    dataset: str,
    params: dict,
    endpoint: str = ELEXON_BMU_VALUES,
    include_dataset_param: bool = True,
) -> list[dict]:
    request_params = params | {"dataset": dataset} if include_dataset_param else params
    res = session.get(endpoint, params=request_params)
    if not res.ok:
        raise ParserException(
            "GB.py",
            f"Exception when fetching storage units error code: {res.status_code}: {res.text}",
            ZONE_KEY,
        )
    return _extract_data_rows(res.json())


def _to_interval_map(
    rows: list[dict],
) -> dict[tuple[str, str, str], tuple[bool, float | None]]:
    mapped: dict[tuple[str, str, str], tuple[bool, float | None]] = {}
    for record in rows:
        key = _extract_storage_key(record)
        if key is None:
            continue
        has_value, value = _extract_dataset_value(record)
        if has_value:
            mapped[key] = (True, value)
    return mapped


def fetch_storage_for_units(units, timestamp: datetime, session: Session):
    storage = 0.0
    settlement_period = 1 + (timestamp.hour * 2) + (timestamp.minute // 30)
    params = {
        "settlementDate": timestamp.strftime("%Y-%m-%d"),
        "settlementPeriod": settlement_period,
        "bmUnit": units,
    }
    boalf_params = {
        "from": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": (timestamp + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bmUnit": units,
    }

    pn_rows = _fetch_storage_dataset(session, "PN", params)
    mel_rows = _fetch_storage_dataset(session, "MELS", params)
    boalf_rows = _fetch_storage_dataset(
        session,
        "BOALF",
        boalf_params,
        endpoint=ELEXON_BOALF_STREAM,
        include_dataset_param=False,
    )

    pn_map = _to_interval_map(pn_rows)
    mel_map = _to_interval_map(mel_rows)
    boalf_map = _to_interval_map(boalf_rows)

    interval_keys = set(pn_map) | set(mel_map) | set(boalf_map)
    for key in interval_keys:
        has_boalf, boalf_val = boalf_map.get(key, (False, None))
        has_pn, pn_val = pn_map.get(key, (False, None))
        has_mel, mel_val = mel_map.get(key, (False, None))

        # order of precedence: BOALF > min(PN, MEL) > PN > 0.
        # MEL is the maximum export limit
        if has_boalf and boalf_val is not None:
            output_act = boalf_val
        elif has_pn and has_mel and pn_val is not None and mel_val is not None:
            output_act = min(pn_val, mel_val)
        elif has_pn and pn_val is not None:
            output_act = pn_val
        else:
            output_act = 0

        minutes = _interval_minutes(key)
        storage += output_act * minutes / 30

    return storage


def fetch_storage(
    session: Session,
    timestamp: datetime,
    hydro_units: list[str],
    battery_units: list[str],
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    storage_mix = StorageMix()
    # Hydro storage
    hydro_storage = fetch_storage_for_units(hydro_units, timestamp, session)
    storage_mix.add_value("hydro", -hydro_storage)
    # Battery storage
    battery_storage = fetch_storage_for_units(battery_units, timestamp, session)
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


def get_battery_units(session: Session, zone_key: ZoneKey) -> list[str]:
    """Fetch battery BMU IDs from the Elexon BMU Fuel Type spreadsheet.

    Filters for units where BMRS FUEL TYPE = "OTHER" and REG FUEL TYPE = "BATTERY".
    """
    res = session.get(
        ELEXON_BMU_FUEL_TYPE_URL,
        headers={"User-Agent": "electricitymaps.com"},
    )
    if not res.ok:
        raise ParserException(
            "GB.py",
            f"Failed to download BMU fuel type spreadsheet: {res.status_code}",
            zone_key,
        )

    wb = load_workbook(BytesIO(res.content), read_only=True, data_only=True)
    ws = wb.active

    battery_units = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        neso_bmu_id = row[0]
        bmrs_fuel_type = row[3]
        reg_fuel_type = row[4]
        if bmrs_fuel_type == "OTHER" and reg_fuel_type == "BATTERY":
            battery_units.append(neso_bmu_id)

    wb.close()
    return battery_units


if __name__ == "__main__":
    for zone_key in ["BE", "CH", "AT", "ES", "FR", "GB", "IT", "NL", "PT"]:
        print(f"fetch_price({zone_key}) ->")
        print(fetch_price(ZoneKey(zone_key)))

    historical_datetime = datetime(2022, 7, 16, 12, tzinfo=timezone.utc)
    print(f"fetch_price(target_datetime={historical_datetime.isoformat()}) ->")
    print(fetch_price(target_datetime=historical_datetime))
