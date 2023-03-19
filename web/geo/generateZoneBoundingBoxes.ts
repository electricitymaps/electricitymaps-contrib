import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mergeZones } from '../scripts/generateZonesConfig.js';
import { saveZoneYaml } from './files.js';
import { getJSON } from './utilities.js';
import { WorldFeatureCollection } from './types.js';
import { Position } from '@turf/turf';

const inputArguments = process.argv.slice(2);

const zonesGeo: WorldFeatureCollection = getJSON(
  path.resolve(fileURLToPath(new URL('world.geojson', import.meta.url)))
);
const zones = mergeZones();

if (inputArguments.length <= 0) {
  console.error(
    'ERROR: Please add a zoneName parameter ("ts-node generateZoneBoundingBoxes.ts DE")'
  );
  process.exit(1);
}

const zoneKey = inputArguments[0];

if (!(zoneKey in zones)) {
  console.error(`ERROR: Zone ${zoneKey} does not exist in configuration`);
  process.exit(1);
}

zonesGeo.features = zonesGeo.features.filter((d) => d.properties.zoneName === zoneKey);

let allCoords = [];
const boundingBoxes: { [key: string]: any } = {};

for (const zone of zonesGeo.features) {
  allCoords = [];
  const geometryType = zone.geometry.type;
  for (const coords1 of zone.geometry.coordinates) {
    for (const coord of coords1[0]) {
      allCoords.push(coord);
    }
  }

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  if (geometryType == 'MultiPolygon') {
    for (const coord of allCoords as Position[]) {
      const lon = coord[0];
      const lat = coord[1];

      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    }
  } else {
    const lon = (allCoords as Position)[0];
    const lat = (allCoords as Position)[1];

    minLon = Math.min(minLon, lon);
    maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  }

  boundingBoxes[zone.properties.zoneName] = [
    [minLon - 0.5, minLat - 0.5],
    [maxLon + 0.5, maxLat + 0.5],
  ];
}

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
