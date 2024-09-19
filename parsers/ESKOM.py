import csv
from datetime import datetime, timedelta, timezone
from logging import Logger, getLogger
from pprint import PrettyPrinter
from zoneinfo import ZoneInfo

from numpy import nan
from requests import Response, Session

from electricitymap.contrib.lib.models.event_lists import ProductionBreakdownList
from electricitymap.contrib.lib.models.events import ProductionMix, StorageMix
from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

pp = PrettyPrinter(indent=4)

TIMEZONE = ZoneInfo("Africa/Johannesburg")
SOURCE = "eskom.co.za"

# Mapping columns to keys
# Helpful: https://www.eskom.co.za/dataportal/glossary/
COLUMN_MAPPING = {
    0: "coal",  # Thermal_Gen_Excl_Pumping_and_SCO
    1: "ignored",  # Eskom_OCGT_SCO_Pumping             changed to ignored since negative oil is not possible, usually [-6, 0]
    2: "ignored",  # Eskom_Gas_SCO_Pumping              changed to ignored since negative gas is not possible, usually -1 or 0
    3: "ignored",  # Hydro_Water_SCO_Pumping            Probably electricity consumed by the plant itself (even) when not generating power. Can be ignored.
    4: "hydro",  # Pumped_Water_SCO_Pumping
    5: "ignored",  # Thermal_Generation                 sum of 0, 1, 2, 3, 4. Can be ignored.
    6: "nuclear",  # Nuclear_Generation
    7: "ignored",  # International_Imports
    8: "oil",  # Eskom_OCGT_Generation
    9: "gas",  # Eskom_Gas_Generation
    10: "oil",  # Dispatchable_IPP_OCGT
    11: "hydro",  # Hydro_Water_Generation
    12: "hydro",  # Pumped_Water_Generation
    13: "ignored",  # IOS_Excl_ILS_and_MLR              Interruption of Supply. Can be ignored.
    14: "ignored",  # ILS_Usage                         Interruptible Load Shed = companies paid not to consume electricity. Can be ignored.
    15: "ignored",  # Manual_Load_Reduction_MLR         MLS = forced load shedding. Can be ignored.
    16: "wind",  # Wind
    17: "solar",  # PV
    18: "solar",  # CSP
    19: "biomass",  # Other_RE - looking at capacity data and the IEA annual balances, other RE is likely to be biomass
}

# Ignored values
# 1, 2, 3, 5, 7, 13, 14, 15
# TODO:
# - 7 (international imports) can be further implemented in exchange function.

STORAGE_IDS = [4, 12]
PRODUCTION_IDS = [0, 6, 8, 9, 10, 11, 16, 17, 18, 19]


def get_url() -> str:
    """Returns the formatted URL"""
    date = datetime.now(timezone.utc)
    return f"https://www.eskom.co.za/dataportal/wp-content/uploads/{date.strftime('%Y')}/{date.strftime('%m')}/Station_Build_Up.csv"


def fetch_production(
    zone_key: ZoneKey = ZoneKey("ZA"),
    session: Session = Session(),
    target_datetime: datetime | None = None,
    logger: Logger = getLogger(__name__),
) -> list[dict]:
    if target_datetime is not None:
        local_target_datetime = target_datetime.astimezone(TIMEZONE)
        local_one_week_ago = datetime.now(TIMEZONE) - timedelta(days=7)

        if local_target_datetime < local_one_week_ago:
            raise NotImplementedError(
                f"No production data is available for {local_target_datetime}."
            )

    res: Response = session.get(get_url())
    if not res.ok:
        raise ParserException(
            "ESKOM.py",
            f"Exception when fetching production for {zone_key}: error when calling url={get_url()}",
            zone_key=zone_key,
        )

    csv_data = csv.reader(res.text.splitlines())

    return_list = ProductionBreakdownList(logger)

    for row in csv_data:
        if row[0] == "Date_Time_Hour_Beginning":
            continue

        returned_datetime = datetime.fromisoformat(row[0]).replace(tzinfo=TIMEZONE)

        returned_production = row[1:]  # First column is datetime

        production = ProductionMix()
        storage = StorageMix()

        if all(value == "" for value in returned_production):
            logger.warning(
                f"Empty data for {returned_datetime} in {zone_key}. Skipping."
            )
            continue
        else:
            for index, prod_data_value in enumerate(returned_production):
                prod_data_value = float(prod_data_value) if prod_data_value else nan
                if index in PRODUCTION_IDS:
                    production.add_value(
                        COLUMN_MAPPING[index],
                        prod_data_value,
                        correct_negative_with_zero=True,
                    )
                elif index in STORAGE_IDS:
                    storage.add_value(COLUMN_MAPPING[index], prod_data_value * -1)

            return_list.append(
                zoneKey=zone_key,
                datetime=returned_datetime,
                production=production,
                storage=storage,
                source=SOURCE,
            )

    return return_list.to_list()


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print("fetch_production() ->")
    pp.pprint(fetch_production())
