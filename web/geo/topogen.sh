#!/bin/bash
set -eu -o pipefail

# Download 10m in order to get smaller states like AU.CT
RESOLUTION=10m
COUNTRIES_FILENAME=ne_${RESOLUTION}_admin_0_map_subunits

STATES_FILENAME=ne_${RESOLUTION}_admin_1_states_provinces_lakes
STATES_FILTER="['AUS', 'AZE', 'BIH', 'BRA', 'CAN', 'CHL', 'DNK', 'ESP', 'GBR', 'GRC', 'IND', 'ITA', 'JPN', 'MEX', 'MYS', 'RUS', 'USA']"

CURRENT_PATH=`dirname "$0"`
BUILD_PATH=$CURRENT_PATH/build

if [ "$CURRENT_PATH" == "geo" ]; then
  PARENT="./"
else
  PARENT="../"
fi

NODE_MODULES_PATH="$PARENT/node_modules/.bin"
DIST_PATH="$PARENT/public/dist"

mkdir -p $DIST_PATH
mkdir -p $BUILD_PATH


if [ ! -e "$BUILD_PATH/${COUNTRIES_FILENAME}.zip" ]; then
  echo "Downloading ${COUNTRIES_FILENAME}.zip"
  curl -z $BUILD_PATH/${COUNTRIES_FILENAME}.zip -o $BUILD_PATH/${COUNTRIES_FILENAME}.zip https://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${COUNTRIES_FILENAME}.zip
fi
unzip -od $BUILD_PATH $BUILD_PATH/${COUNTRIES_FILENAME}.zip

if [ ! -e "$BUILD_PATH/${STATES_FILENAME}.zip" ]; then
  echo "Downloading ${STATES_FILENAME}.zip"
  curl -z $BUILD_PATH/${STATES_FILENAME}.zip -o $BUILD_PATH/${STATES_FILENAME}.zip https://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${STATES_FILENAME}.zip
fi
unzip -od $BUILD_PATH $BUILD_PATH/${STATES_FILENAME}.zip

# Move 3rd party shapes to build
cp -r $CURRENT_PATH/third_party_maps/* $BUILD_PATH

# Extract metadata
echo "Extract metadata"
("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/${COUNTRIES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.properties' \
)> $BUILD_PATH/world_countries_props.json

("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/${STATES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.properties' \
)> $BUILD_PATH/world_states_props.json

("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/Canary_Islands.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.properties' \
)> $BUILD_PATH/third_party_props.json

# We could use a country filter here to remove unneeded natural earth shapes.
# Parse countries
echo 'Parsing countries..'
("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/${COUNTRIES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" '(d.id = (d.properties.ISO_A3 != "-99") ? d.properties.ISO_A3 : d.properties.ADM0_A3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.SU_A3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
  | "$NODE_MODULES_PATH/ndjson-filter" "d.id" \
)> $BUILD_PATH/tmp_countries.json

# Parse states
echo 'Parsing states..'
("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/${STATES_FILENAME}.shp \
  | "$NODE_MODULES_PATH/ndjson-map" '(d.id = d.properties.adm0_a3, d)' \
  | "$NODE_MODULES_PATH/ndjson-filter" "d.id && ${STATES_FILTER}.indexOf(d.id) != -1"
)> $BUILD_PATH/tmp_states.json

# Parse 3rd party
echo 'Parsing 3rd party..'
("$NODE_MODULES_PATH/shp2json" -n $BUILD_PATH/Canary_Islands.shp \
  | "$NODE_MODULES_PATH/ndjson-map" 'd.id = d.properties.NAME, d' \
  | "$NODE_MODULES_PATH/ndjson-filter" "d.id" \
)> $BUILD_PATH/tmp_thirdparty.json

# Generate final geometries
node $CURRENT_PATH/generate-geometries.js
