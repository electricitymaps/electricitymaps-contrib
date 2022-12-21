import path from 'path';

const args = process.argv.slice(2);

import { mergeZones } from '../generate-zones-config';
import { saveZoneYaml } from './files';
import { getJSON } from './utilities';

const zonesGeo = getJSON(path.resolve(__dirname, './world.geojson'));
const zones = mergeZones();

if (args.length <= 0) {
  console.error(
    'ERROR: Please add a zoneName parameter ("node generate-zone-bounding-boxes.js DE")'
  );
  process.exit(1);
}

const zoneKey = args[0];

if (!(zoneKey in zones)) {
  console.error(`ERROR: Zone ${zoneKey} does not exist in configuration`);
  process.exit(1);
}

zonesGeo.features = zonesGeo.features.filter((d) => d.properties.zoneName === zoneKey);

let allCoords: number[] = [];
const boundingBoxes: { [key: string]: any } = {};

zonesGeo.features.forEach((zone) => {
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

for (const [zoneKey, bbox] of Object.entries(boundingBoxes)) {
  // do not add new entries to zones/*.yaml, do not add RU because it crosses the 180th meridian
  if (!(zoneKey in zones) || zoneKey === 'RU' || zoneKey === 'RU-FE') {
    continue;
  }
  // do not modifiy current bounding boxes
  if (zones[zoneKey].bounding_box) {
    continue;
  }
  zones[zoneKey].bounding_box = [bbox[0], bbox[1]];

  saveZoneYaml(zoneKey, zones[zoneKey]);
}

console.error(
  `Done, check /config/zones/${zoneKey}.yaml to verify that the result looks good!`
);
