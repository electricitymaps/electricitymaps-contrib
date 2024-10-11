import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { Position } from '@turf/turf';
import yaml from 'js-yaml';

import { saveZoneYaml } from './files.js';
import { WorldFeatureCollection, ZoneConfig } from './types.js';
import { getJSON } from './utilities.js';

const inputArguments = process.argv.slice(2);

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));

const zonesGeo: WorldFeatureCollection = getJSON(
  path.resolve(currentDirectory, 'world.geojson')
);

if (inputArguments.length <= 0) {
  console.error(
    'ERROR: Please add a zoneName parameter ("ts-node --esm generateZoneBoundingBoxes.ts DE")'
  );
  process.exit(1);
}

const zoneKey = inputArguments[0];

const zonePath = path.resolve(currentDirectory, `../../config/zones/${zoneKey}.yaml`);
const zoneConfig = yaml.load(fs.readFileSync(zonePath, 'utf8')) as ZoneConfig;

if (!zoneConfig) {
  console.error(`ERROR: Zone ${zoneKey} does not exist in configuration`);
  process.exit(1);
}

let zoneFeatures = zonesGeo.features.filter((d) => d.properties.zoneName === zoneKey);
let isAggregate = false;
if (zoneFeatures.length <= 0) {
  console.info(`Zone ${zoneKey} does not exist in geojson, using subzones instead`);
  isAggregate = true;
  zoneFeatures = zonesGeo.features.filter((d) => d.properties.countryKey === zoneKey);
}
zonesGeo.features = zoneFeatures;

let allCoords: Position[] = [];
let boundingBoxes: { [key: string]: number[][] } = {};

for (const zone of zonesGeo.features) {
  allCoords = [];
  const geometryType = zone.geometry.type;
  for (const coords1 of zone.geometry.coordinates) {
    for (const coord of coords1[0]) {
      allCoords.push(coord as Position);
    }
  }

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  if (geometryType == 'MultiPolygon') {
    for (const coord of allCoords) {
      const lon = coord[0];
      const lat = coord[1];

      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    }
  } else {
    const lon = allCoords[0] as unknown as number;
    const lat = allCoords[1] as unknown as number;

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

if (isAggregate) {
  const averageBoundingBox: number[][] = [
    [200, 200],
    [-200, -200],
  ];
  for (const bbox of Object.values(boundingBoxes)) {
    averageBoundingBox[0][0] = Math.min(averageBoundingBox[0][0], bbox[0][0]); // minX
    averageBoundingBox[0][1] = Math.min(averageBoundingBox[0][1], bbox[0][1]); // minY
    averageBoundingBox[1][0] = Math.max(averageBoundingBox[1][0], bbox[1][0]); // maxX
    averageBoundingBox[1][1] = Math.max(averageBoundingBox[1][1], bbox[1][1]); // maxY
  }
  boundingBoxes = {}; // Reset subzone bounding boxes
  boundingBoxes[zoneKey] = averageBoundingBox;
}

for (const [zoneKey, bbox] of Object.entries(boundingBoxes)) {
  // do not add new entries to zones/*.yaml, do not add RU because it crosses the 180th meridian
  if (zoneKey === 'RU' || zoneKey === 'RU-FE' || zoneKey === 'US-AK') {
    console.log('IGNORING', zoneKey, 'because it is crossing the 180th meridian');
    continue;
  }
  // do not modifiy current bounding boxes
  if (zoneConfig.bounding_box) {
    continue;
  }

  zoneConfig.bounding_box = [bbox[0], bbox[1]];

  saveZoneYaml(zoneKey, zoneConfig);
}

console.error(
  `Done, check /config/zones/${zoneKey}.yaml to verify that the result looks good!`
);
