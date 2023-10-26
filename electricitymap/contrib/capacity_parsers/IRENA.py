from datetime import datetime

import pandas as pd

from electricitymap.contrib.config import ZoneKey

"""The data needs to be downloaded from the IRENA statistics page: https://www.irena.org/Data/Downloads/IRENASTAT
Click on Power Capacity and Generation and select Installed electricity capacity (MW) by Country/area, Technology, Grid connection and Year
You can then choose the country (or countries) and the year that you want to download data for. You should select all technologies and grid connection.
Choose Excel (xlsx) in the dropdown menu at the bottom of the page and click on Continue.

This parser is developed so that it will read the data from the downloaded file and return a dictionary with the capacity data for the selected year. """

IRENA_ZONES = ["IL", "IS", "LK", "NI", "GF", "PF"]

IRENA_ZONES_MAPPING = {
    "Albania": "AL",
    "Argentina": "AR",
    "Aruba": "AW",
    "Austria": "AT",
    "Bangladesh": "BD",
    "Belgium": "BE",
    "Bolivia (Plurinational State of)": "BO",
    "Bosnia and Herzegovina": "BA",
    "Bulgaria": "BG",
    "Chile": "CL-SEN",
    "China, Hong Kong Special Administrative Region": "HK",
    "Chinese Taipei": "TW",
    "Colombia": "CO",
    "Costa Rica": "CR",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Czechia": "CZ",
    "Estonia": "EE",
    "Faroe Islands": "FO",
    "Finland": "FI",
    "France": "FR",
    "French Guiana": "GF",
    "French Polynesia": "PF",
    "Georgia": "GE",
    "Germany": "DE",
    "Greece": "GR",
    "Guadeloupe": "GP",
    "Guatemala": "GT",
    "Honduras": "HN",
    "Hungary": "HU",
    "Iceland": "IS",
    "Indonesia": "ID",
    "Ireland": "IE",
    "Israel": "IL",
    "Kosovo": "XK",
    "Kuwait": "KW",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malaysia": "MY",
    "Malta": "MT",
    "Martinique": "MQ",
    "Mexico": "MX",
    "Mongolia": "MN",
    "Montenegro": "ME",
    "Netherlands (Kingdom of the)": "NL",
    "New Zealand": "NZ",
    "Nicaragua": "NI",
    "Nigeria": "NG",
    "North Macedonia": "MK",
    "Panama": "PA",
    "Peru": "PE",
    "Poland": "PL",
    "Portugal": "PT",
    "Puerto Rico": "PR",
    "Qatar": "QA",
    "Republic of Korea (the)": "KR",
    "Republic of Moldova (the)": "MD",
    "Réunion": "RE",
    "Romania": "RO",
    "Saudi Arabia": "SA",
    "Serbia": "RS",
    "Singapore": "SG",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "South Africa": "ZA",
    "Spain": "ES",
    "Sri Lanka": "LK",
    "Switzerland": "CH",
    "Thailand": "TH",
    "Türkiye": "TR",
    "Ukraine": "UA",
    "United Arab Emirates (the)": "AE",
    "United Kingdom of Great Britain and Northern Ireland (the)": "GB",
    "Uruguay": "UY",
}

IRENA_MODE_MAPPING = {
    "Biogas": "biomass",
    "Geothermal energy": "geothermal",
    "Liquid biofuels": "biomass",
    "Marine energy": "unknown",
    "Mixed Hydro Plants": "hydro",
    "Offshore wind energy": "wind",
    "Onshore wind energy": "wind",
    "Other non-renewable energy": "unknown",
    "Pumped storage": "hydro storage",
    "Renewable hydropower": "hydro",
    "Renewable municipal waste": "biomass",
    "Solar photovoltaic": "solar",
    "Solar thermal energy": "solar",
    "Solid biofuels": "biomass",
    "Coal and peat": "coal",
    "Fossil fuels n.e.s.": "unknown",
    "Natural gas": "gas",
    "Nuclear": "nuclear",
    "Oil": "oil",
    "Other non-renewable energy": "unknown",
}

SPECIFIC_MODE_MAPPING = {"IS": {"Fossil fuels n.e.s.": "oil"}}


def map_variable_to_mode(row: pd.Series) -> pd.DataFrame:
    zone = row["country"]
    variable = row["mode"]
    if zone in SPECIFIC_MODE_MAPPING:
        if variable in SPECIFIC_MODE_MAPPING[zone]:
            row["mode"] = SPECIFIC_MODE_MAPPING[zone][variable]
        else:
            row["mode"] = IRENA_MODE_MAPPING[variable]
    else:
        row["mode"] = IRENA_MODE_MAPPING[variable]
    return row


def get_capacity_data(path: str, target_datetime: datetime) -> dict:
    df = pd.read_excel(path, skipfooter=26)
    df = df.rename(
        columns={
            "Installed electricity capacity (MW) by Country/area, Technology, Grid connection and Year": "country",
            "Unnamed: 1": "mode",
            "Unnamed: 2": "category",
            "Unnamed: 3": "year",
            "Unnamed: 4": "value",
        }
    )
    df["country"] = df["country"].ffill()
    df["mode"] = df["mode"].ffill()
    df = df.dropna(axis=0, how="all")

    df_filtered = df.loc[df["country"].isin(list(IRENA_ZONES_MAPPING.keys()))]
    df_filtered["country"] = df_filtered["country"].map(IRENA_ZONES_MAPPING)

    df_filtered = df_filtered.apply(map_variable_to_mode, axis=1)
    df_filtered = df_filtered.dropna(axis=0, how="any")
    df_filtered = (
        df_filtered.groupby(["country", "mode", "year"])[["value"]].sum().reset_index()
    )
    capacity_dict = format_capacity(target_datetime, df_filtered)
    return capacity_dict


def format_capacity(target_datetime: datetime, data: pd.DataFrame) -> dict:
    df = data.copy()
    # filter by target_datetime.year
    df = df.loc[df["year"] == target_datetime.year]

    all_capacity = {}

    for zone in df["country"].unique():
        df_zone = df.loc[df["country"] == zone]
        zone_capacity = {}
        for idx, data in df_zone.iterrows():
            zone_capacity[data["mode"]] = {
                "value": round(float(data["value"]), 0),
                "source": "IRENA",
                "datetime": target_datetime.strftime("%Y-%m-%d"),
            }
        all_capacity[zone] = zone_capacity
    return all_capacity


def fetch_production_capacity_for_all_zones(
    path: str, target_datetime: datetime
) -> None:
    all_capacity = get_capacity_data(path, target_datetime.year)

    all_capacity = {k: v for k, v in all_capacity.items() if k in IRENA_ZONES}
    print(f"Fetched capacity data from IRENA for {target_datetime.year}")
    return all_capacity


def fetch_production_capacity(
    path: str, target_datetime: datetime, zone_key: ZoneKey
) -> None:
    all_capacity = get_capacity_data(path, target_datetime)
    zone_capacity = all_capacity[zone_key]
    if zone_capacity:
        print(
            f"Updated capacity for {zone_key} in {target_datetime.year}: \n{zone_capacity}"
        )
        return zone_capacity
    else:
        raise ValueError(f"No capacity data for {zone_key} in {target_datetime.year}")
