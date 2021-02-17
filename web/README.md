*This file should host other explanations. Yours are welcome.*

## How is world.json generated?

The world map data is open source and provided by [NACIS](http://nacis.org/initiatives/natural-earth/).

To generate a new world.json run the following command from the web directory after making changes:

```sh
docker-compose run --rm web ./topogen.sh
```

### `topogen.sh`

The file `topogen.sh` does the following:

- download data from NACIS, at 1:10M scale. Both countries and states data are downloaded,
and added to the `web/build` folder
- other data (at 12.01.2018, only Canaries Islands) is added to the `build` folder
- the module `shp2json` is used to convert the shp data to the GeoJSON format
- `generate-geometries.js` is then called

### `generate-geometries.js`

The variables `zoneDefinitions` should be updated manually to reflect intended changes in mapping between electricityMap zones and NACIS geometries. It relates each zone from the electricityMap to how it is described by data from NACIS (or third party). A zone can correspond to a country, a group of countries, a state, a group of states...

The function `geomerge` merges a list of GeoJSON Polygons or MultiPolygons into a single
multi-polygon. This allows to merge a group of geometries into a single one.

According to `zoneDefinition`, a single GeoJSON MultiPolygon is created for each zone, by
grouping all geometries corresponding to that zone.

Finally, the module `topojson` converts the GeoJSON into into the
TopoJSON format, which is a more compressed format than geoJSON. It only stores arcs that are used multiple times once. We also perform some simplifications and project points
on a grid. All together, this allows to convert a ~`24MB` file to a ~`1MB` one.

The final file is named `world.json` and is the one sent to the client.

## `generate-zone-bounding-boxes.js`

You can create bounding boxes for new or existing zones in `config/zones.json`:
1) Run: `docker-compose run --rm web ./topogen.sh`
2) Update the zone you want to update in `config/zones.json` with `"bounding_box": null`
3) Run: `node generate-zone-bounding-boxes.js`

## Useful tips

- [geojson.io](https://geojson.io) is a great tool for visualizing and editing coordinates
- We currently can't generate coordinates for small islands --> any PRs for fixing this without compromising too much on bundle size is very welcome!
