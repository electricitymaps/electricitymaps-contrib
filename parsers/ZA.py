import csv
from datetime import datetime, timedelta
from logging import Logger, getLogger
from pprint import PrettyPrinter
from typing import List, Optional

from pytz import timezone
from requests import Response, Session

from electricitymap.contrib.lib.types import ZoneKey
from parsers.lib.exceptions import ParserException

pp = PrettyPrinter(indent=4)

TIMEZONE = "Africa/Johannesburg"

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
    19: "unknown",  # Other_RE
}

# Ignored values
# 1, 2, 3, 5, 7, 13, 14, 15
# TODO:
# - 7 (international imports) can be further implemented in exchange function.

STORAGE_IDS = [4, 12]
PRODUCTION_IDS = [0, 6, 8, 9, 10, 11, 16, 17, 18, 19]


def get_url() -> str:
    """Returns the formatted URL"""
    date = datetime.utcnow()
    return f"https://www.eskom.co.za/dataportal/wp-content/uploads/{date.strftime('%Y')}/{date.strftime('%m')}/Station_Build_Up.csv"


def fetch_production(
    zone_key: ZoneKey = ZoneKey("ZA"),
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:
    if target_datetime is not None:
        local_target_datetime = target_datetime.astimezone(timezone(TIMEZONE))
        local_one_week_ago = datetime.now(timezone(TIMEZONE)) - timedelta(days=7)

        if local_target_datetime < local_one_week_ago:
            raise NotImplementedError(
                f"No production data is available for {local_target_datetime}."
            )

    res: Response = session.get(get_url())
    if not res.ok:
        raise ParserException(
            "ZA.py",
            f"Exception when fetching production for {zone_key}: error when calling url={get_url()}",
            zone_key=zone_key,
        )

    csv_data = csv.reader(res.text.splitlines())

    return_list = []

    for row in csv_data:
        if row[0] == "Date_Time_Hour_Beginning":
            continue

        returned_datetime = datetime.fromisoformat(row[0]).replace(
            tzinfo=timezone(TIMEZONE)
        )

        returned_production = row[1:]  # First column is datetime

        production = {}
        storage = {}

        for index, prod_data_value in enumerate(returned_production):
            prod_data_value = float(prod_data_value)
            if index in PRODUCTION_IDS:
                if COLUMN_MAPPING[index] in production.keys():
                    production[COLUMN_MAPPING[index]] += (
                        prod_data_value if prod_data_value >= 0 else 0
                    )
                else:
                    production[COLUMN_MAPPING[index]] = (
                        prod_data_value if prod_data_value >= 0 else 0
                    )
            elif index in STORAGE_IDS:
                if COLUMN_MAPPING[index] in storage.keys():
                    storage[COLUMN_MAPPING[index]] += prod_data_value * -1
                else:
                    storage[COLUMN_MAPPING[index]] = prod_data_value * -1

        return_list.append(
            {
                "zoneKey": zone_key,
                "datetime": returned_datetime,
                "production": production,
                "storage": storage,
                "source": "eskom.co.za",
            }
        )

    return return_list


if __name__ == "__main__":
    """Main method, never used by the Electricity Maps backend, but handy for testing."""

    print("fetch_production() ->")
    pp.pprint(fetch_production())
