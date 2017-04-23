#!/bin/bash
set -eu -o pipefail

COUNTRIES_FILENAME=ne_50m_admin_0_map_subunits
# COUNTRIES_FILTER='...'

STATES_FILENAME=ne_50m_admin_1_states_provinces_lakes
STATES_FILTER='CAN' # Use '\|' to separate entries

# To install tools:
# npm install -g d3-geo-projection ndjson-cli shapefile topojson

mkdir -p build
curl -z build/${COUNTRIES_FILENAME}.zip -o build/${COUNTRIES_FILENAME}.zip http://naciscdn.org/naturalearth/50m/cultural/${COUNTRIES_FILENAME}.zip
unzip -od build build/${COUNTRIES_FILENAME}.zip
curl -z build/${STATES_FILENAME}.zip -o build/${STATES_FILENAME}.zip http://naciscdn.org/naturalearth/50m/cultural/${STATES_FILENAME}.zip
unzip -od build build/${STATES_FILENAME}.zip

# Clear tmp.json
> build/tmp.json

# Parse countries
(shp2json -n build/${COUNTRIES_FILENAME}.shp \
| ndjson-map '(d.id = (d.properties.iso_a3 != "-99") ? d.properties.iso_a3 : d.properties.adm0_a3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.su_a3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
#| grep "$COUNTRIES_FILTER"
)>> build/tmp.json

# Parse states
(shp2json -n build/${STATES_FILENAME}.shp \
| ndjson-map '(d.id = d.properties.sr_adm0_a3, d.oldProps = d.properties, d.properties = {}, d.properties.subid = d.oldProps.su_a3, d.properties.code_hasc = d.oldProps.code_hasc, delete d.oldProps, d)' \
| grep "$STATES_FILTER"
)>> build/tmp.json

# Merge & simplify
(geo2topo -q 1e5 -n countries=<(cat build/tmp.json | geostitch -n) \
| topomerge land=countries \
| toposimplify -f -p 0.01
)> app/world_50m.json

(shp2json -n build/${STATES_FILENAME}.shp \
  | ndjson-map 'd.properties' \
  | grep "$STATES_FILTER" \
)> world_states_50m_props.json
(shp2json -n build/${COUNTRIES_FILENAME}.shp \
  | ndjson-map 'd.properties' \
  #| grep "$COUNTRIES_FILTER" \
)> world_countries_50m_props.json

rm -rvf build
