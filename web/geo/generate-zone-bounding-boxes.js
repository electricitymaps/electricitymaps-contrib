const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);

function readNDJSON(filePath) {
  return fs
    .readFileSync(path.resolve(__dirname, filePath), 'utf8')
    .split('\n')
    .filter((d) => d !== '')
    .map(JSON.parse);
}

let zones = readNDJSON('../public/dist/zonegeometries.json');
if (args.length > 0) {
  zones = zones.filter((d) => d.properties.zoneName === args[0]);
}

let allCoords = [];
const boundingBoxes = {};

zones.forEach((zone) => {
  allCoords = [];
  zone.geometry.coordinates.forEach((coords1) => {
    coords1[0].forEach((coord) => allCoords.push(coord));
  });

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  allCoords.forEach((coord) => {
    const lon = coord[0];
    const lat = coord[1];

    minLon = Math.min(minLon, lon);
    maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  });

  boundingBoxes[zone.properties.zoneName] = [
    [minLon - 0.5, minLat - 0.5],
    [maxLon + 0.5, maxLat + 0.5],
  ];
});

zones = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../../config/zones.json'), 'utf8'));

for (const [zone, bbox] of Object.entries(boundingBoxes)) {
  // do not add new entries to zones.json, do not add RU because it crosses the 180th meridian
  if (!(zone in zones) || zone === 'RU' || zone === 'RU-FE') continue;
  // do not modifiy current bounding boxes
  if (zones[zone].bounding_box) continue;
  zones[zone].bounding_box = [bbox[0], bbox[1]];
}

fs.writeFileSync(
  path.resolve(__dirname, '../../config/zones.json'),
  JSON.stringify(zones, null, 2)
);
