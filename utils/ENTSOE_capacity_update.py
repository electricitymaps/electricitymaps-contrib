#!/usr/bin/env python3

import os
import sys
import argparse
import pandas as pd
import json
import pathlib

from parsers.ENTSOE import ENTSOE_PARAMETER_DESC, ENTSOE_PARAMETER_GROUPS

ZONESFILE = pathlib.Path(__file__).parent.parent / "config" / "zones.json"


def update_zone(zone, data, zonesfile):
	with open(zonesfile) as zf:
		zones = json.load(zf)

	if zone not in zones:
		raise ValueError("Zone {} does not exist in the zonesfile".format(zone))

	zones[zone]["capacity"].update(data)

	with open(zonesfile, "w") as zf:
		json.dump(zones, zf, indent=2)
		zf.write("\n")


def aggregate_data(data):
	"""Aggregates data the way it is stated in
	   parsers.ENTSOE.ENTSOE_PARAMETER_GROUPS"""
	
	# choose the column with the most current data
	# assume keys start with YYYY
	sorted_keys = list(sorted(data.keys()))
	data = data[sorted_keys[-1]]

	categories = dict(ENTSOE_PARAMETER_GROUPS["production"])
	categories.update(ENTSOE_PARAMETER_GROUPS["storage"])

	aggregated = {}
	for group, category_abbreviations in categories.items():
		category_descriptions = list(map(lambda x: ENTSOE_PARAMETER_DESC[x], category_abbreviations))
		aggregated[group] = sum(data[c] for c in category_descriptions)

	return aggregated


def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("--zonesfile", default=ZONESFILE)
	parser.add_argument("zone", help="The zone abbreviation (e.g. AT)")
	parser.add_argument("data_file", help="The csv file from ENTSOE containing the installed capacities")
	return parser.parse_args()


def main():
	args = parse_args()
	
	zone = args.zone
	zonesfile = args.zonesfile
	data_file = args.data_file

	if not os.path.exists(zonesfile):
		print("ERROR: Zonesfile {} does not exist.".format(zonesfile),
			  file=sys.stderr)
		sys.exit(1)
	if not os.path.exists(data_file):
		print("ERROR: Data file {} does not exist.".format(data_file),
			  file=sys.stderr)
		sys.exit(1)
	
	data = pd.read_csv(data_file).set_index("Production Type").to_dict()
	aggregated_data = aggregate_data(data)

	print("Aggregated capacities: {}".format(json.dumps(aggregated_data)))
	print("Updating zone {}".format(zone))

	update_zone(zone, aggregated_data, zonesfile)


if __name__ == "__main__":
	main()