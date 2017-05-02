#!/bin/bash
set -eu -o pipefail

# Download 10m in order to get smaller states like AU.CT
RESOLUTION=10m
COUNTRIES_FILENAME=ne_${RESOLUTION}_admin_0_map_subunits

STATES_FILENAME=ne_${RESOLUTION}_admin_1_states_provinces_lakes
STATES_FILTER="['CAN', 'AUS']"

# To install tools:
# npm install -g d3-geo-projection ndjson-cli shapefile topojson

# mkdir -p build
# curl -z build/${COUNTRIES_FILENAME}.zip -o build/${COUNTRIES_FILENAME}.zip http://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${COUNTRIES_FILENAME}.zip
# unzip -od build build/${COUNTRIES_FILENAME}.zip
# curl -z build/${STATES_FILENAME}.zip -o build/${STATES_FILENAME}.zip http://naciscdn.org/naturalearth/${RESOLUTION}/cultural/${STATES_FILENAME}.zip
# unzip -od build build/${STATES_FILENAME}.zip

# Extract metadata
(shp2json -n build/${COUNTRIES_FILENAME}.shp \
  | ndjson-map 'd.properties' \
)> world_countries_props.json
(shp2json -n build/${STATES_FILENAME}.shp \
  | ndjson-map 'd.properties' \
)> world_states_props.json

# Clear tmp.json
> build/tmp.json
# Parse countries
echo 'parsing countries..'
(shp2json -n build/${COUNTRIES_FILENAME}.shp \
  | ndjson-map '(d.id = (d.properties.ISO_A3 != "-99") ? d.properties.ISO_A3 : d.properties.ADM0_A3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.SU_A3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
  | ndjson-filter 'd.id' \
)>> build/tmp.json
# Parse states
echo 'parsing states..'
(shp2json -n build/${STATES_FILENAME}.shp \
  | ndjson-map '(d.id = d.properties.adm0_a3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.su_a3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
  | ndjson-filter "d.id && ${STATES_FILTER}.indexOf(d.id) != -1"
)>> build/tmp.json
# Merge & simplify
echo 'merging and simplifying..'
(geo2topo -q 1e5 -n countries=<(cat build/tmp.json | geostitch -n) \
  | topomerge land=countries \
  | toposimplify -f -p 0.01
)> app/world.json
echo '..done'

#rm -rvf build
