#!/bin/bash
set -eu -o pipefail

# To install tools:
# npm install -g d3-geo-projection ndjson-cli shapefile topojson

mkdir -p build
curl -z build/ne_50m_admin_0_map_subunits.zip -o build/ne_50m_admin_0_map_subunits.zip http://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_map_subunits.zip
unzip -od build build/ne_50m_admin_0_map_subunits.zip
chmod a-x build/ne_50m_admin_0_map_subunits.*

geo2topo -q 1e5 -n countries=<( \
  shp2json -n build/ne_50m_admin_0_map_subunits.shp \
    | ndjson-map '(d.id = d.properties.adm0_a3, d.subid = d.properties.su_a3, delete d.properties, d)' \
    | geostitch -n) \
| topomerge land=countries \
> app/world_50m.json
shp2json -n build/ne_50m_admin_0_map_subunits.shp \
| ndjson-map 'd.properties' \
> world_50m_props.json
rm -rvf build
