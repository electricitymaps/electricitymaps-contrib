import json
import os

def relative_path(script_reference_path, rel_path):
    # __file__ should be passed as script_reference_path
    script_path = os.path.abspath(
        script_reference_path)  # i.e. /path/to/dir/foobar.py
    script_dir = os.path.split(script_path)[0]  # i.e. /path/to/dir/
    return os.path.join(script_dir, rel_path)


# Prepare zone bounding boxes
ZONE_BOUNDING_BOXES = {}

# Read parser import list from config jsons
ZONES_CONFIG = json.load(open(relative_path(
    __file__, '../config/zones.json')))

# Read all zones
for zone_id, zone_config in ZONES_CONFIG.items():
    if 'bounding_box' in zone_config:
        ZONE_BOUNDING_BOXES[zone_id] = zone_config['bounding_box']

# Read parser import list from config jsons
ZONES_CONFIG = json.load(open(relative_path(
    __file__, '../config/zones.json')))
EXCHANGES_CONFIG = json.load(open(relative_path(
    __file__, '../config/exchanges.json')))
ZONE_NEIGHBOURS = {}
for k, v in EXCHANGES_CONFIG.items():
    zone_names = k.split('->')
    pairs = [
        (zone_names[0], zone_names[1]),
        (zone_names[1], zone_names[0])
    ]
    for zone_name_1, zone_name_2 in pairs:
        if zone_name_1 not in ZONE_NEIGHBOURS:
            ZONE_NEIGHBOURS[zone_name_1] = set()
        ZONE_NEIGHBOURS[zone_name_1].add(zone_name_2)
