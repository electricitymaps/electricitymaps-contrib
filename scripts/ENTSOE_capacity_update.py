#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import sys
from copy import deepcopy

import pandas as pd
import requests
import xmltodict
import yaml
from utils import ROOT_PATH, run_shell_command

from electricitymap.contrib.config import CONFIG_DIR, ZONES_CONFIG, ZoneKey
from parsers.ENTSOE import (
    ENTSOE_DOMAIN_MAPPINGS,
    ENTSOE_PARAMETER_DESC,
    ENTSOE_PARAMETER_GROUPS,
)


def update_zone(zone_key: ZoneKey, data: dict) -> None:
    if zone_key not in ZONES_CONFIG:
        raise ValueError("Zone {} does not exist in the zones config".format(zone_key))

    _new_zone_config = deepcopy(ZONES_CONFIG[zone_key])
    _new_zone_config["capacity"].update(data)
    # sort keys
    _new_zone_config["capacity"] = {
        k: _new_zone_config["capacity"][k] for k in sorted(_new_zone_config["capacity"])
    }
    ZONES_CONFIG[zone_key] = _new_zone_config

    with open(
        CONFIG_DIR.joinpath(f"zones/{zone_key}.yaml"), "w", encoding="utf-8"
    ) as f:
        f.write(yaml.dump(_new_zone_config, default_flow_style=False))


def aggregate_data(data: dict) -> dict:
    """Aggregates data the way it is stated in
    parsers.ENTSOE.ENTSOE_PARAMETER_GROUPS"""
    categories = dict(ENTSOE_PARAMETER_GROUPS["production"])
    categories.update(ENTSOE_PARAMETER_GROUPS["storage"])

    aggregated = {}
    for group, category_abbreviations in categories.items():
        aggregated[group] = sum(data.get(c, 0) for c in category_abbreviations)

    return aggregated


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-token", help="Security token of the ENTSOE API")
    parser.add_argument("zone_key", help="The zone key abbreviation (e.g. AT)")
    parser.add_argument(
        "data_file",
        nargs="?",
        help="The csv file from ENTSOE containing the installed capacities",
    )
    return parser.parse_args()


def parse_from_entsoe_api(zone_key: ZoneKey, token: str) -> dict:
    """Parses installed generation capacities from the ENTSOE API,
    see https://transparency.entsoe.eu/content/static_content/Static%20content/web%20api/Guide.html#_reference_documentation"""

    if zone_key not in ENTSOE_DOMAIN_MAPPINGS:
        print(
            "Zone {} does not exist in the ENTSOE domain mapping".format(zone_key),
            file=sys.stderr,
        )
        exit(1)

    domain = ENTSOE_DOMAIN_MAPPINGS[zone_key]

    # TODO not sure whether selecting the date always works like that
    date = datetime.datetime.now().strftime("%Y%m%d")
    url = (
        "https://transparency.entsoe.eu/api?securityToken={token}"
        "&documentType=A68&processType=A33&in_Domain={domain}"
        "&periodStart={date}0000&periodEnd={date}0000".format(
            token=token, domain=domain, date=date
        )
    )
    response = requests.get(url)
    if response.status_code != 200:
        print(
            "ERROR: Request to ENTSOE API failed with status {}".format(
                response.status_code
            ),
            file=sys.stderr,
        )
        exit(1)

    data = xmltodict.parse(response.text)

    result = {}
    try:
        root = data["GL_MarketDocument"]
        for time_series in root["TimeSeries"]:
            generation_type = time_series["MktPSRType"]["psrType"]
            value = time_series["Period"]["Point"]["quantity"]
            result[generation_type] = int(value)
    except Exception as e:
        raise ValueError(
            "Data for zone {} could not be retrieved from ENTSOE".format(zone_key), e
        )

    return result


def parse_from_csv(filepath: str) -> dict:
    data = pd.read_csv(filepath).set_index("Production Type").to_dict()

    # choose the column with the most current data
    # assume keys start with YYYY
    sorted_keys = list(sorted(data.keys()))
    data = data[sorted_keys[-1]]

    inverse_mapping = {v: k for k, v in ENTSOE_PARAMETER_DESC.items()}
    return {inverse_mapping[k]: v for k, v in data.items() if k in inverse_mapping}


def main():
    args = parse_args()

    zone_key = args.zone_key
    data_file = args.data_file

    if data_file is not None:
        if not os.path.exists(data_file):
            print(
                "ERROR: Data file {} does not exist.".format(data_file), file=sys.stderr
            )
            sys.exit(1)
        data = parse_from_csv(data_file)
    else:
        token = args.api_token
        if token is None:
            print(
                "ERROR: If no CSV file is given, the option --api-token must be provided",
                file=sys.stderr,
            )
            exit(1)

        data = parse_from_entsoe_api(zone_key, token)

    aggregated_data = aggregate_data(data)

    print("Aggregated capacities: {}".format(json.dumps(aggregated_data)))
    print("Updating zone {}".format(zone_key))

    update_zone(zone_key, aggregated_data)

    run_shell_command(
        f"npx prettier --write {ROOT_PATH / 'config/zones/'}", cwd=ROOT_PATH
    )


if __name__ == "__main__":
    main()
