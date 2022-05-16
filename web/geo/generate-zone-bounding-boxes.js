const path = require('path');

const args = process.argv.slice(2);

const { getJSON } = require('./utilities');
const { getZonesJson, saveZonesJson } = require('./files');

let zones = getJSON(path.resolve(__dirname, './world.geojson'));

if (args.length <= 0) {
  console.error('ERROR: Please add a zoneName parameter ("node generate-zone-bounding-boxes.js DE")');
  process.exit(1);
}
zones.features = zones.features.filter((d) => d.properties.zoneName === args[0]);

let allCoords = [];
const boundingBoxes = {};

zones.features.forEach((zone) => {
  allCoords = [];
  const geometryType = zone.geometry.type;
  zone.geometry.coordinates.forEach((coords1) => {
    coords1[0].forEach((coord) => allCoords.push(coord));
  });

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  if (geometryType == 'MultiPolygon') {
    allCoords.forEach((coord) => {
      const lon = coord[0];
      const lat = coord[1];

      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });
  } else {
    const lon = allCoords[0];
    const lat = allCoords[1];

    minLon = Math.min(minLon, lon);
    maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  }

  boundingBoxes[zone.properties.zoneName] = [
    [minLon - 0.5, minLat - 0.5],
    [maxLon + 0.5, maxLat + 0.5],
  ];
});

zones = getZonesJson();

for (const [zone, bbox] of Object.entries(boundingBoxes)) {
  // do not add new entries to zones.json, do not add RU because it crosses the 180th meridian
  if (!(zone in zones) || zone === 'RU' || zone === 'RU-FE') {
    continue;
  }
  // do not modifiy current bounding boxes
  if (zones[zone].bounding_box) {
    continue;
  }
  zones[zone].bounding_box = [bbox[0], bbox[1]];
}

saveZonesJson(zones);

console.error('Done, check /config/zones.json to verify that the result looks good!');
