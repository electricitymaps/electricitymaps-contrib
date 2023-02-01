# Overview

The world.geojson file is a geojson file containing all geographies and metadata for all zones visible on the electricityMap app. The zones are also used in the backend of Electricity Maps.

You can see tutorials and more information on our [wiki](https://github.com/electricityMaps/electricitymaps-contrib/wiki/Edit-world-geometries).

# How to update world.geojson

To update geographies on the app

1. Create manual changes on world.geojson
2. Run `pnpm generate-world` from web folder

This will validate and generate the new world.json which is a compressed version of the world.geojson.
