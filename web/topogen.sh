#!/bin/bash
set -eu -o pipefail

FILENAME=ne_50m_admin_0_map_subunits
#Check ne_50m_admin_1_states_provinces_lakes for US & Canada provinces.

# To install tools:
# npm install -g d3-geo-projection ndjson-cli shapefile topojson

mkdir -p build
curl -z build/${FILENAME}.zip -o build/${FILENAME}.zip http://naciscdn.org/naturalearth/50m/cultural/${FILENAME}.zip
unzip -od build build/${FILENAME}.zip
chmod a-x build/${FILENAME}.*

geo2topo -q 1e5 -n countries=<( \
  shp2json -n build/${FILENAME}.shp \
    | ndjson-map '(d.id = d.properties.adm0_a3, d.subid = d.properties.su_a3, delete d.properties, d)' \
    | geostitch -n) \
| topomerge land=countries \
> app/world_50m.json

shp2json -n build/${FILENAME}.shp \
| ndjson-map 'd.properties' \
> world_50m_props.json
rm -rvf build
