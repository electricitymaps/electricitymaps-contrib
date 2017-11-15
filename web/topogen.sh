#!/bin/bash
set -eu -o pipefail

# Download 10m in order to get smaller states like AU.CT
RESOLUTION=10m
COUNTRIES_FILENAME=ne_${RESOLUTION}_admin_0_map_subunits

STATES_FILENAME=ne_${RESOLUTION}_admin_1_states_provinces
STATES_FILTER="['AUS', 'BRA', 'CAN', 'CHL', 'IND']"

NODE_MODULES_PATH="node_modules/.bin"

mkdir -p build

if [ ! -e "build/${COUNTRIES_FILENAME}.zip" ]; then
    echo "Downloading ${COUNTRIES_FILENAME}.zip"
    curl -z build/${COUNTRIES_FILENAME}.zip -o build/${COUNTRIES_FILENAME}.zip http://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${COUNTRIES_FILENAME}.zip
    unzip -od build build/${COUNTRIES_FILENAME}.zip
fi

if [ ! -e "build/${STATES_FILENAME}.zip" ]; then
    curl -z build/${STATES_FILENAME}.zip -o build/${STATES_FILENAME}.zip http://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${STATES_FILENAME}.zip
    unzip -od build build/${STATES_FILENAME}.zip
fi


# Extract metadata
echo "Extract metadata"
("$NODE_MODULES_PATH/shp2json" -n build/${COUNTRIES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.properties' \
)> build/world_countries_props.json

("$NODE_MODULES_PATH/shp2json" -n build/${STATES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.properties' \
)> build/world_states_props.json

# Parse countries
echo 'Parsing countries..'
("$NODE_MODULES_PATH/shp2json" -n build/${COUNTRIES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" '(d.id = (d.properties.ISO_A3 != "-99") ? d.properties.ISO_A3 : d.properties.ADM0_A3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.SU_A3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
  | "$NODE_MODULES_PATH/ndjson-filter" 'd.id' \
)> build/tmp.json

# Parse states
echo 'Parsing states..'
("$NODE_MODULES_PATH/shp2json" -n build/${STATES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" '(d.id = d.properties.adm0_a3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.su_a3, d.properties.code_hasc = d.oldProps.code_hasc, d.properties.hasc_maybe = d.oldProps.hasc_maybe, d.properties.fips = d.oldProps.fips, d.properties.adm1_code = d.oldProps.adm1_code, d.properties.region_cod = d.oldProps.region_cod, delete d.oldProps, d)' \
  | "$NODE_MODULES_PATH/ndjson-filter" "d.id && ${STATES_FILTER}.indexOf(d.id) != -1"
)>> build/tmp.json

# Merge & simplify
echo 'Merging and simplifying..'
("$NODE_MODULES_PATH/geo2topo" -q 1e5 -n countries=<(cat build/tmp.json | "$NODE_MODULES_PATH/geostitch" -n) \
  | "$NODE_MODULES_PATH/topomerge" land=countries \
  | "$NODE_MODULES_PATH/toposimplify" -f -p 0.01
)> app/world.json

echo 'Done'
