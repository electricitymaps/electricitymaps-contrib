from datetime import datetime
from logging import Logger, getLogger
from pprint import PrettyPrinter
from typing import List, Optional

from arrow import get, now
from requests import Response, Session

pp = PrettyPrinter(indent=4)

TIMEZONE = "Africa/Johannesburg"


def get_url() -> str:
    """Returns the formatted URL"""
    date = datetime.utcnow()
    return f"https://www.eskom.co.za/dataportal/wp-content/uploads/{date.strftime('%Y')}/{date.strftime('%m')}/Station_Build_Up.csv"


def fetch_production(
    zone_key: str = "ZA",
    session: Session = Session(),
    target_datetime: Optional[datetime] = None,
    logger: Logger = getLogger(__name__),
) -> List[dict]:

    if target_datetime is not None:
        local_target_datetime = get(target_datetime).to(TIMEZONE)
        local_one_week_ago = now(TIMEZONE).shift(days=-7)

        if local_target_datetime < local_one_week_ago:
            raise NotImplementedError(
                f"No production data is available for {local_target_datetime}."
            )

    res: Response = session.get(get_url())
    assert res.status_code == 200, (
        "Exception when fetching production for "
        f"{zone_key}: error when calling url={get_url()}"
    )

    csv_data = res.text.split("\r\n")
    production_csv_data = {}

    for _, row in enumerate(csv_data[1:]):
        date = row.split(";")[0]
        if len(date) > 10:
            date = get(date, "YYYY-MM-DD HH:mm:ss")
            row_data = row.split(";")[1:]
            if row_data[0] != "":
                production_csv_data[date] = [
                    float(item.replace(",", ".")) for item in row.split(";")[1:]
                ]

    # Mapping columns to keys
    # Helpful: https://www.eskom.co.za/dataportal/glossary/
    column_mapping = {
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

    all_data = []

    for _, (datetime_key, prod_data) in enumerate(production_csv_data.items()):

        # The production values (MW) should never be negative. Use None, or omit the key if # a specific production mode is not known.
        # ---
        # storage values can be both positive (when storing energy) or negative (when the
        # storage is discharged).

        data = {
            "zoneKey": zone_key,
            "datetime": datetime_key.datetime,
            "production": {
                "coal": 0.0,
                "gas": 0.0,
                "hydro": 0.0,
                "nuclear": 0.0,
                "oil": 0.0,
                "solar": 0.0,
                "wind": 0.0,
                "unknown": 0.0,
            },
            "storage": {"hydro": 0.0},
            "source": " https://www.eskom.co.za",
        }

        storage_inversion_idcs = [4, 12]
        production_idcs = [0, 6, 8, 9, 10, 11, 16, 17, 18, 19]

        # Ignored values
        # 1, 2, 3, 5, 7, 13, 14, 15
        # TODO:
        # - 7 (international imports) can be further implemented in exchange function.

        for j, prod_data_value in enumerate(prod_data):
            if j in storage_inversion_idcs:
                data["storage"][column_mapping[j]] = round(
                    data["storage"][column_mapping[j]] + float(prod_data_value) * -1,
                    13,
                )
            elif j in production_idcs:
                data["production"][column_mapping[j]] = round(
                    data["production"][column_mapping[j]] + float(prod_data_value),
                    13,
                )

        all_data.append(data)

    return all_data


if __name__ == "__main__":
    """Main method, never used by the Electricity Map backend, but handy for testing."""

    print("fetch_production() ->")
    pp.pprint(fetch_production())
