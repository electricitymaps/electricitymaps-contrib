#!/usr/bin/env python3

"""
This script updates capacity for each year from 2017 to 2023 using EMBER data.
"""

import subprocess
import logging

def run_capacity_update(target_datetime):
    """Run capacity update command for a specific date"""
    cmd = [
        "poetry", "run", "python", "-m", "capacity_update",
        "--zone", "AR",
        "--source", "None",
        "--target_datetime", target_datetime,
        "--update_aggregate", "False"
    ]
    subprocess.run(cmd, check=True)

def main():
    """Update capacity for each year from 2017 to 2023"""
    target_date = "2021-01-01"
    print(f"Updating capacity for {target_date}")
    run_capacity_update(target_date)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main() 