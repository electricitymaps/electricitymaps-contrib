#!/usr/bin/env python3
"""
poetry run python scripts/remove_zone.py DK-DK1
"""
import argparse
import os
from glob import glob

from utils import LOCALE_FILE_PATHS, ROOT_PATH, JsonFilePatcher, run_shell_command

from electricitymap.contrib.config import ZoneKey
from electricitymap.contrib.config.constants import EXCHANGE_FILENAME_ZONE_SEPARATOR


def remove_zone(zone_key: ZoneKey):
    # Remove zone config
    try:
        os.remove(ROOT_PATH / f"config/zones/{zone_key}.yaml")
    except FileNotFoundError:
        pass

    # Remove exchanges for that zone
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
        except FileNotFoundError:
            pass

    # TODO: we could check if part of subZoneNames
    # TODO: we could detect parsers that are only used by this zone
    #       so we can clean those files up.

    for locale_file in LOCALE_FILE_PATHS:
        with JsonFilePatcher(locale_file, indent=4) as f:
            zone_short_name = f.content["zoneShortName"]
            if zone_key in zone_short_name:
                del zone_short_name[zone_key]

    for api_version in ["v3", "v4"]:
        try:
            with JsonFilePatcher(
                ROOT_PATH / f"mockserver/public/{api_version}/state"
            ) as f:
                data = f.content["data"]
                if zone_key in data["countries"]:
                    del data["countries"][zone_key]

                for k in list(data["exchanges"].keys()):
                    if k.startswith(f"{zone_key}->") or k.endswith(f"->{zone_key}"):
                        del data["exchanges"][k]
        except FileNotFoundError:
            pass

    for api_version in ["v5"]:
        for state_level in ["daily", "hourly", "monthly", "yearly"]:
            try:
                with JsonFilePatcher(
                    ROOT_PATH
                    / f"mockserver/public/{api_version}/state/{state_level}.json"
                ) as f:
                    data = f.content["data"]
                    if zone_key in data["countries"]:
                        del data["countries"][zone_key]

                    for k in list(data["exchanges"].keys()):
                        if k.startswith(f"{zone_key}->") or k.endswith(f"->{zone_key}"):
                            del data["exchanges"][k]
            except FileNotFoundError:
                pass

    geo_json_path = ROOT_PATH / "web/geo/world.geojson"
    with JsonFilePatcher(geo_json_path) as f:
        new_features = [
            f for f in f.content["features"] if f["properties"]["zoneName"] != zone_key
        ]
        f.content["features"] = new_features

    run_shell_command(f"npx prettier --write {geo_json_path}", cwd=ROOT_PATH)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zone", help="The zone abbreviation (e.g. AT)")
    args = parser.parse_args()
    zone = args.zone

    print(f"Removing {zone}")
    remove_zone(zone)
    print(
        f"NOTE: There is still a bit of cleaning up to do. Try searching for files and references."
    )
    print('Please rerun "pnpm generate-world" inside the web folder.')


if __name__ == "__main__":
    main()
