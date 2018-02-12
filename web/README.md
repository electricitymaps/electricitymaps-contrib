*This file should host other explanations. Yours are welcome.* 

## How is world.json generated?

The world data is open source and provided by [NACIS](http://nacis.org/initiatives/natural-earth/).

### `topogen.sh`

The file `topogen.sh` does the following :

- download data from NACIS, at 1:10M scale. Both countries and states data are downloaded,
and added to the `web/build` folder
- other data (at 12.01.2018, only Canaries Islands) is added to the `build` folder
- the module `shp2json` is used to convert the shp data to the geoJSON format
- `generate-geometries.js` is then called

### `generate-geometries.js`

The variables `zoneDefinitions` relates each zone from the Electricity Map to how it is
described by data from NACIS (or third party). A zone can correspond to a country, a 
group of country, a state, a group of states...

The function `geomerge` merges a list of geoJSON Polygons or MultiPolygons into a single
multi-polygon. This allows to merge a group of geometries into a single one.

According to `zoneDefinition`, a single geoJSON MultiPolygon is created for each zone, by
grouping all geometries corresponding to that zone.

Finally, the module `topojson` converts the geoJSON into into the 
topoJSON format, which is a more compressed format than geoJSON. It only stores once
arcs that are used multiple times. We also perform some simplifications and project points
on a grid. All together, this allows to convert a ~`24MB` file to a ~`1MB` one.

The final file is named `world.json` and is the one sent to the client.
