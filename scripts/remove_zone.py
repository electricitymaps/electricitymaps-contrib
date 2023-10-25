#!/usr/bin/env python3

"""
This script helps to remove a zone (including the zone config and exchanges).

Example usage:
  poetry run python scripts/remove_zone.py DK-DK1
"""

import argparse
import os
import re
from glob import glob
from shutil import move

from utils import (
    LOCALE_FILE_PATHS,
    ROOT_PATH,
    JsonFilePatcher,
    YamlFilePatcher,
    run_shell_command,
)

from electricitymap.contrib.config.constants import EXCHANGE_FILENAME_ZONE_SEPARATOR
from electricitymap.contrib.lib.types import ZoneKey

PRETTIER_CONFIG_PATH = ROOT_PATH / "web/.prettierrc.json"


def remove_config(zone_key: ZoneKey):
    try:
        os.remove(ROOT_PATH / f"config/zones/{zone_key}.yaml")
        print(f"🧹 Removed {zone_key}.yaml")
    except FileNotFoundError:
        pass


def remove_from_parent_config(zone_key: ZoneKey):
    # Remove zone-key from subZoneNames in parent yaml file
    parent_config_path = ROOT_PATH / f"config/zones/{zone_key.split('-')[0]}.yaml"
    if parent_config_path.exists():
        with YamlFilePatcher(parent_config_path) as f:
            sub_zone_names = f.content["subZoneNames"]
            if zone_key in sub_zone_names:
                sub_zone_names.remove(zone_key)
        run_shell_command(
            f"npx prettier@2 --config {PRETTIER_CONFIG_PATH} --write {parent_config_path}",
            cwd=ROOT_PATH,
        )


def remove_exchanges(zone_key: ZoneKey):
    def _is_zone_in_exchange(exchange_config_path: str) -> bool:
        exchange_key = exchange_config_path.split("/")[-1].split(".")[0]
        return zone_key in exchange_key.split(EXCHANGE_FILENAME_ZONE_SEPARATOR)

    exchanges = [
        e
        for e in glob(str(ROOT_PATH / "config/exchanges/*.yaml"))
        if _is_zone_in_exchange(e)
    ]
    for exchange in exchanges:
        try:
            os.remove(exchange)
            print(f"🧹 Removed {exchange.split('/')[-1]}")
        except FileNotFoundError:
            pass


def remove_translations(zone_key: ZoneKey):
    for locale_file in LOCALE_FILE_PATHS:
        with JsonFilePatcher(locale_file, indent=2) as f:
            zone_short_name = f.content["zoneShortName"]
            if zone_key in zone_short_name:
                del zone_short_name[zone_key]


def remove_mockserver_data(zone_key: ZoneKey):
    for API_version in ["v6", "v7"]:
        for state_level in ["daily", "hourly", "monthly", "yearly"]:
            try:
                with JsonFilePatcher(
                    ROOT_PATH
                    / f"mockserver/public/{API_version}/state/{state_level}.json"
                ) as f:
                    data = f.content["data"]
                    if zone_key in data["zones"]:
                        del data["zones"][zone_key]

                    for k in list(data["exchanges"].keys()):
                        if k.startswith(f"{zone_key}->") or k.endswith(f"->{zone_key}"):
                            del data["exchanges"][k]
            except FileNotFoundError:
                pass


def remove_geojson_entry(zone_key: ZoneKey):
    geo_json_path = ROOT_PATH / "web/geo/world.geojson"
    with JsonFilePatcher(geo_json_path, indent=None) as f:
        new_features = [
            f for f in f.content["features"] if f["properties"]["zoneName"] != zone_key
        ]
        f.content["features"] = new_features

    run_shell_command(
        f"npx prettier@2 --config {PRETTIER_CONFIG_PATH} --write {geo_json_path}",
        cwd=ROOT_PATH,
    )
    run_shell_command(
        f"pnpm generate-world",
        cwd=ROOT_PATH / "web",
    )


def move_parser_to_archived(zone_key: ZoneKey):
    parser_path = ROOT_PATH / f"parsers/{zone_key}.py"
    if parser_path.exists():
        run_shell_command(
            f"git mv {parser_path} {ROOT_PATH / 'parsers/archived'}", cwd=ROOT_PATH
        )
        print(f"🧹 Moved parser to /archived folder")


def find_files_mentioning_zone(text):
    """Search for the zone_key across all files in contrib."""
    IGNORED_PATHS = [
        "mobileapp/ios",
        "mobileapp/android",
        "node_modules",
        "dist",
        "archived",
    ]
    VALID_EXTENSIONS = (
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".yaml",
        ".json",
        ".md",
        ".html",
    )
    results = []
    for root, dirs, files in os.walk(ROOT_PATH):
        if any([ignored_path in root for ignored_path in IGNORED_PATHS]):
            continue
        for file in files:
            if file.endswith(VALID_EXTENSIONS):
                with open(os.path.join(root, file), "r") as f:
                    if re.search(text, f.read()):
                        # print the relative path
                        results.append(
                            os.path.relpath(os.path.join(root, file), ROOT_PATH)
                        )
    if not results:
        print(f'🧹 Found no additional files mentioning "{text}" in contrib repository.')
        return

    print(
        f"❗️ Found {len(results)} files mentioning {text}, please manually clean these files:"
    )
    for result in results:
        print(f"  - {result}")


def main():
    """Removes a zone by from a bunch of places and lists additional files mentioning the zone key."""

    if os.name != "posix":
        print("This script only works on Unix-like systems.")
        exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("zone", help="The zone abbreviation (e.g. AT)")
    args = parser.parse_args()
    zone_key = args.zone

    print(f"Removing {zone_key}...\n")

    remove_config(zone_key)
    remove_from_parent_config(zone_key)
    remove_exchanges(zone_key)
    remove_translations(zone_key)
    remove_mockserver_data(zone_key)
    remove_geojson_entry(zone_key)
    move_parser_to_archived(zone_key)
    # For legacy reasons, a subzone parser can both use dash and underscore
    # in the file name so we need to search for both
    move_parser_to_archived(zone_key.replace("-", "_"))
    find_files_mentioning_zone(zone_key)

    print("\n✔  All done!")


if __name__ == "__main__":
    main()
