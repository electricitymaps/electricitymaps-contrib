"""
This script checks if the config filenames are valid.

This is run as a part of the CI but can be run locally to ensure all filenames
are valid before you commit the changes.

Usage:
    uv run python scripts/validate_config_filenames.py
"""

import os


def main():
    zone_files = os.listdir("config/zones")
    exchange_files = os.listdir("config/exchanges")
    has_zone_error: bool = False
    has_exchange_error: bool = False

    print("Checking config files...")
    print("Checking if zone files are valid...")

    # Check if zone files are valid. Zone files must be uppercase.
    for file in zone_files:
        if file.endswith(".yaml") or file.endswith(".yml"):
            file = file.replace(".yaml", "") or file.replace(".yml", "")
            if file != file.upper():
                has_zone_error = True
                print(f"ERROR: {file} is not uppercase")
    if not has_zone_error:
        print("All zone filenames are valid!")
    else:
        print("There are errors in the above zone filenames!")

    # Check if exchange files are valid. Exchange files must be sorted and
    # uppercase.
    for file in exchange_files:
        if file.endswith(".yaml") or file.endswith(".yml"):
            file = file.replace(".yaml", "") or file.replace(".yml", "")
            exchange_keys = file.split("_")
            sorted_exchange_keys = sorted(exchange_keys)
            if file != file.upper():
                has_exchange_error = True
                print(f"ERROR: {file} is not uppercase")
            if exchange_keys != sorted_exchange_keys:
                has_exchange_error = True
                print(f"ERROR: {file} is not sorted")
    if not has_exchange_error:
        print("All exchange filenames are valid!")
    else:
        print("There are errors in the above exchange filenames!")

    if has_zone_error or has_exchange_error:
        exit(1)


if __name__ == "__main__":
    main()
