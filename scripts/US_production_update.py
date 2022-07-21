import argparse
import json

from parsers.EIA import EIA_PRODUCTION_GROUPS

ZONESFILE = pathlib.Path(__file__).parent.parent / "config" / "zones.json"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zonesfile", default=ZONESFILE)
    parser.add_argument("--api-token", help="Security token of the iEA API")
    parser.add_argument("zone", help="The zone abbreviation (e.g. AT)")
    parser.add_argument(
        "data_file",
        nargs="?",
        help="The csv file from ENTSOE containing the installed capacities",
    )
    return parser.parse_args()


def aggregate_data(data):
    """Aggregates data the way it is stated in
    parsers.EIA.EIA_PRODUCTION_GROUPS"""
    zones = dict(EIA_PRODUCTION_GROUPS)

    aggregated = {}
    for group, main_zone in zones.items():
        aggregated[group] = sum(data.get(c, 0) for c in main_zone)

    return aggregated


def update_zone(zone, data, zonesfile):
    with open(zonesfile) as zf:
        zones = json.load(zf)

    if zone not in zones:
        raise ValueError("Zone {} does not exist in the zonesfile".format(zone))

    zones[zone]["production"].update(data)

    with open(zonesfile, "w") as zf:
        json.dump(zones, zf, indent=2)
        zf.write("\n")


def main():
    args = parse_args()

    zone = args.zone
    zonesfile = args.zonesfile
    data_file = args.data_file

    aggregated_data = aggregate_data(data)

    print("Aggregated capacities: {}".format(json.dumps(aggregated_data)))
    print("Updating zone {}".format(zone))

    update_zone(zone, aggregated_data, zonesfile)
