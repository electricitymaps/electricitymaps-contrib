"""
Price parser that uses the RTE-FRANCE API
Production parser that uses the NESO and Elexon APIs
The storage values are computed using the Elexon API, aggregating the data per unit. To debug this use you can use:

PRINT_DETAILS=hydro_storage uv run test_parser GB     -> which prints the hydro storage details, also including the minute details
PRINT_DETAILS=battery_storage uv run test_parser GB   -> which prints the battery storage details, excluding the minute details, since there are too many battery units to print the minute details for each one

"""

import os
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
        start_datetime = datetime.now(tz=ZoneInfo("UTC")) - timedelta(hours=4)
        end_datetime = None
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
        timestamp = datetime.fromisoformat(row["DATETIME"]).replace(
            tzinfo=ZoneInfo("UTC")
        )

        if timestamp < start_datetime:
            continue
        if end_datetime is not None and timestamp > end_datetime:
            break

        production_mix = ProductionMix()

        for neso_key, emaps_key in NESO_TO_PRODUCTION_MIX_MAPPING.items():
            production_mix.add_value(emaps_key, float(row[neso_key]))

        storage_mix = fetch_storage(session, timestamp, hydro_units, battery_units)

        production_list.append(
            zoneKey=zone_key,
            datetime=timestamp,
            production=production_mix,
            storage=storage_mix,
            source="neso.energy, elexon.co.uk",
        )

    return production_list.to_list()


def fetch_storage(
    session: Session,
    timestamp: datetime,
    hydro_units: list[str],
    battery_units: list[str],
    logger: Logger = getLogger(__name__),
) -> list[dict] | dict:
    debug = os.environ.get("PRINT_DETAILS", "").lower()
    storage_mix = StorageMix()
    # Hydro storage
    hydro_storage = fetch_storage_for_units(
        hydro_units,
        timestamp,
        session,
        print_details=debug == "hydro_storage",
        print_minute_details=debug == "hydro_storage",
    )
    storage_mix.add_value("hydro", -hydro_storage)
    # Battery storage
    battery_storage = fetch_storage_for_units(
        battery_units,
        timestamp,
        session,
        print_details=debug == "battery_storage",
        print_minute_details=False,
    )
    storage_mix.add_value("battery", -battery_storage)
    return storage_mix


def fetch_storage_for_units(
    units: list[str],
    timestamp: datetime,
    session: Session,
    print_details: bool = False,
    print_minute_details: bool = False,
) -> float:
    """Compute the aggregate storage MW for a list of BMU units over one settlement period.

    Args:
        units: List of BMU unit identifiers (e.g. ["T_CRUA-1", "T_CRUA-2"]).
        timestamp: The UTC start of the 30-minute settlement period.

    Returns:
        The sum of average MW across all units for this period. Positive
        values mean the units are generating (exporting); negative values
        mean they are consuming (importing/charging).

    Data sources fetched from Elexon:
        - PN  (Physical Notification): the unit's declared schedule.
        - MELS (Maximum Export Limit): upper MW bound per unit.
        - MILS (Minimum Import Limit): lower MW bound per unit (negative).
        - BOALF (Bid-Offer Acceptance Level): System Operator instructions
          that override PN when present.

    Cross-period coverage:
        The Elexon API filters in ways that can miss records spanning across
        settlement period boundaries:

        - The /balancing/physical/all endpoint (PN, MELS, MILS) returns data
          for a single settlement period. A record whose timeFrom falls in
          the previous period but whose timeTo extends into ours would only
          be returned when querying the previous period. We therefore fetch
          both the current AND previous settlement periods and merge them.

        - The /datasets/BOALF/stream endpoint filters by TimeFrom — it only
          returns records whose timeFrom falls within the [from, to) query
          window. A long-running BOALF acceptance (e.g. timeFrom=20:00,
          timeTo=23:00) would be missed if we only query from 22:30. We
          use a 4-hour lookback to catch these long-running acceptances.
          The per-minute resolution logic then correctly picks only records
          that actually cover each minute in our 30-minute window.
    """
    settlement_date = timestamp.strftime("%Y-%m-%d")
    settlement_period = 1 + (timestamp.hour * 2) + (timestamp.minute // 30)
    prev_date, prev_period = _previous_settlement_period(
        settlement_date, settlement_period
    )

    current_physical_params = {
        "settlementDate": settlement_date,
        "settlementPeriod": settlement_period,
        "bmUnit": units,
    }
    prev_physical_params = {
        "settlementDate": prev_date,
        "settlementPeriod": prev_period,
        "bmUnit": units,
    }

    boalf_params = {
        "from": (timestamp - timedelta(hours=4)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": (timestamp + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bmUnit": units,
    }

    pn_rows = _fetch_storage_dataset(
        session, "PN", current_physical_params
    ) + _fetch_storage_dataset(session, "PN", prev_physical_params)
    mels_rows = _fetch_storage_dataset(
        session, "MELS", current_physical_params
    ) + _fetch_storage_dataset(session, "MELS", prev_physical_params)
    mils_rows = _fetch_storage_dataset(
        session, "MILS", current_physical_params
    ) + _fetch_storage_dataset(session, "MILS", prev_physical_params)
    boalf_rows = _fetch_storage_dataset(
        session,
        "BOALF",
        boalf_params,
        endpoint=ELEXON_BOALF_STREAM,
        include_dataset_param=False,
    )

    boalf_by_unit = _group_by_unit(boalf_rows)
    pn_by_unit = _group_by_unit(pn_rows)
    mels_by_unit = _group_by_unit(mels_rows)
    mils_by_unit = _group_by_unit(mils_rows)

    if print_details:
        print(
            f"\n  [{timestamp.strftime('%Y-%m-%d %H:%M')}] {len(units)} units, "
            f"API returned: {len(boalf_rows)} BOALF, {len(pn_rows)} PN, "
            f"{len(mels_rows)} MELS, {len(mils_rows)} MILS rows"
        )

    total_storage = 0.0
    for unit in units:
        if print_details:
            n_boalf = len(boalf_by_unit.get(unit, []))
            n_pn = len(pn_by_unit.get(unit, []))
            print(f"  {unit}: {n_boalf} BOALF recs, {n_pn} PN recs", end="")
        unit_mw = _compute_unit_storage_mw(
            boalf_records=boalf_by_unit.get(unit, []),
            pn_records=pn_by_unit.get(unit, []),
            mels_records=mels_by_unit.get(unit, []),
            mils_records=mils_by_unit.get(unit, []),
            period_start=timestamp,
            print_details=print_details,
            print_minute_details=print_minute_details,
        )
        total_storage += unit_mw

    if print_details:
        print(f"  TOTAL: {total_storage:.1f} MW")
    return total_storage


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
    return None


def _parse_iso_datetime(dt_str: str) -> datetime:
    """Parse an ISO 8601 datetime string (ending in 'Z') to a UTC-aware datetime."""
    return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _group_by_unit(rows: list[dict]) -> dict[str, list[dict]]:
    """Group API response rows by BMU unit identifier."""
    grouped: dict[str, list[dict]] = {}
    for record in rows:
        ids_found = (
            {str(record["nationalGridBmUnit"])}
            if record.get("nationalGridBmUnit")
            else set()
        )
        for unit_id in ids_found:
            grouped.setdefault(unit_id, []).append(record)
    return grouped


def _get_boalf_value_at_minute(
    records: list[dict], minute_dt: datetime
) -> float | None:
    """Determine the BOALF MW level for a single unit at a specific minute.

    BOALF (Bid-Offer Acceptance Level Flagged) records represent instructions
    from the System Operator to a generation/storage unit. Multiple BOALF
    records can cover the same minute — each identified by an acceptanceNumber.
    A higher acceptanceNumber represents a more recent instruction that
    supersedes earlier ones.

    Algorithm:
      1. Find all BOALF records whose [timeFrom, timeTo) interval covers
         the minute.
      2. Among those, pick the record with the highest acceptanceNumber.
      3. Return its levelFrom (the MW level at the start of the interval).

    We use levelFrom rather than interpolating between levelFrom and levelTo.
    In practice, "body" records (spanning many minutes) have
    levelFrom == levelTo, and "ramp" records are only 1 minute long, so
    the error from not interpolating is negligible.

    Returns None if no BOALF record covers this minute, signalling the
    caller to fall back to PN data.
    """
    best_acceptance = -1
    best_value: float | None = None

    for rec in records:
        time_from = _parse_iso_datetime(rec["timeFrom"])
        time_to = _parse_iso_datetime(rec["timeTo"])

        if time_from <= minute_dt < time_to:
            acceptance = rec.get("acceptanceNumber", 0)
            if acceptance > best_acceptance:
                level = _to_float(rec.get("levelFrom"))
                if level is not None:
                    best_acceptance = acceptance
                    best_value = level

    return best_value


def _get_level_at_minute(records: list[dict], minute_dt: datetime) -> float | None:
    """Determine the MW level from a PN/MELS/MILS dataset at a specific minute.

    Physical Notification (PN), Maximum Export Limit (MELS), and Minimum
    Import Limit (MILS) datasets share the same record structure with
    timeFrom/timeTo and levelFrom/levelTo fields. Their intervals typically
    align to settlement period boundaries but are not guaranteed to.

    For a given minute, finds the record whose [timeFrom, timeTo) interval
    covers it and returns its levelFrom.

    Returns None if no record covers this minute.
    """
    for rec in records:
        time_from_str = rec.get("timeFrom") or rec.get("startTime") or ""
        time_to_str = rec.get("timeTo") or rec.get("endTime") or ""
        if not time_from_str or not time_to_str:
            continue

        time_from = _parse_iso_datetime(time_from_str)
        time_to = _parse_iso_datetime(time_to_str)

        if time_from <= minute_dt < time_to:
            return _to_float(rec.get("levelFrom"))

    return None


def _compute_unit_storage_mw(
    boalf_records: list[dict],
    pn_records: list[dict],
    mels_records: list[dict],
    mils_records: list[dict],
    period_start: datetime,
    period_minutes: int = 30,
    print_details: bool = False,
    print_minute_details: bool = False,
) -> float:
    """Compute the average MW output for one storage unit over a 30-minute period.

    Resolves the effective MW value at each minute in [period_start,
    period_start + period_minutes) using the following precedence:

      1. BOALF available  → use it directly. If multiple BOALF records
         cover a minute, the highest acceptanceNumber wins.
      2. PN available, and MELS and/or MILS available → clamp PN to
         the [MILS, MELS] range. MELS is the Maximum Export Limit
         (upper bound), MILS is the Minimum Import Limit (lower bound,
         typically negative for storage importing/charging).
      3. PN available, no limits → use PN as-is.
      4. No data at all → assume 0 MW.

    Returns the average MW over the period (sum of per-minute values
    divided by period_minutes).
    """
    total = 0.0
    boalf_minutes = 0
    pn_minutes = 0
    zero_minutes = 0
    minute_details: list[str] = []

    for m in range(period_minutes):
        minute_dt = period_start + timedelta(minutes=m)
        ts = minute_dt.strftime("%H:%M")

        boalf_value = _get_boalf_value_at_minute(boalf_records, minute_dt)
        pn_value = _get_level_at_minute(pn_records, minute_dt)
        mels_value = _get_level_at_minute(mels_records, minute_dt)
        mils_value = _get_level_at_minute(mils_records, minute_dt)

        if boalf_value is not None:
            total += boalf_value
            boalf_minutes += 1
            if boalf_value != 0 or (pn_value is not None and pn_value != 0):
                pn_str = f"|PN:{pn_value:.0f}" if pn_value is not None else ""
                minute_details.append(f"{ts}=BOALF:{boalf_value:.0f}{pn_str}")
            continue

        if pn_value is not None:
            clamped = pn_value
            if mels_value is not None:
                clamped = min(clamped, mels_value)
            if mils_value is not None:
                clamped = max(clamped, mils_value)
            total += clamped
            pn_minutes += 1
            if clamped != 0:
                extra = ""
                if clamped != pn_value:
                    extra = f"(raw:{pn_value:.0f})"
                minute_details.append(f"{ts}=PN:{clamped:.0f}{extra}")
            continue

        zero_minutes += 1

    avg_mw = total / period_minutes
    if print_details:
        summary = (
            f"    {boalf_minutes}xBOALF {pn_minutes}xPN {zero_minutes}xNODATA"
            f" → avg={avg_mw:.1f} MW"
        )
        print(summary)
        if print_minute_details and minute_details:
            for m in minute_details:
                print(f"      {m}")
    return avg_mw


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


def _previous_settlement_period(
    settlement_date: str, settlement_period: int
) -> tuple[str, int]:
    """Return (date, period) for the settlement period immediately before the given one.

    Settlement periods are numbered 1–48 within a day (each 30 minutes).
    Period 1 on day D is preceded by period 48 on day D-1.
    """
    if settlement_period > 1:
        return settlement_date, settlement_period - 1
    prev_date = (
        datetime.strptime(settlement_date, "%Y-%m-%d") - timedelta(days=1)
    ).strftime("%Y-%m-%d")
    return prev_date, 48


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
            hydro_storage_units.append(r["nationalGridBmUnit"])

    return hydro_storage_units


def get_battery_units(session: Session, zone_key: ZoneKey) -> list[str]:
    """Fetch battery BMU IDs from the Elexon BMU Fuel Type spreadsheet.

    Filters for units where BMRS FUEL TYPE = "OTHER" and REG FUEL TYPE = "BATTERY".
    """
    res = session.get(
        ELEXON_BMU_FUEL_TYPE_URL,
        headers={"User-Agent": "Mozilla/5.0"},
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
