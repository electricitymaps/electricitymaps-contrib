*This file should host other explanations. Yours are welcome.*

## Local development

See [local development setup](https://github.com/tmrowco/electricitymap-contrib/wiki/Set-up-local-environment#running-the-frontend-map) in the wiki.


## How is world.json generated?

The world map data is open source and provided by [NACIS](http://nacis.org/initiatives/natural-earth/).

To generate a new world.json run the following command from the web directory after making changes:

```sh
docker-compose run --rm web ./geo/topogen.sh
```

### `topogen.sh`

The file `topogen.sh` does the following:

- download data from NACIS, at 1:10M scale. Both countries and states data are downloaded,
and added to the `web/build` folder
- other data (at 12.01.2018, only Canaries Islands) is added to the `build` folder
- the module `shp2json` is used to convert the shp data to the GeoJSON format
- `geo/generate-geometries.js` is then called which simplifies and compresses the geojson data
- The output is `world.json` which is sent to the client

### `geometries-config.js`

The variables `zoneDefinitions` should be updated manually to reflect intended changes in mapping between electricityMap zones and NACIS geometries. It relates each zone from the electricityMap to how it is described by data from NACIS (or third party). A zone can correspond to a country, a group of countries, a state, a group of states...


## `generate-zone-bounding-boxes.js`

You can create bounding boxes for new or existing zones in `config/zones.json`:
1) Run: `docker-compose run --rm web ./geo/topogen.sh`
2) Update the zone you want to update in `config/zones.json` with `"bounding_box": null`
3) Run: `node geo/generate-zone-bounding-boxes.js`

## Useful tips

- [geojson.io](https://geojson.io) is a great tool for visualizing and editing coordinates
- We currently can't generate coordinates for small islands --> any PRs for fixing this without compromising too much on bundle size is very welcome!
