import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';
import { saveZoneYaml } from './files.js';
import { getJSON } from './utilities.js';
import { WorldFeatureCollection, ZoneConfig } from './types.js';
import { Position } from '@turf/turf';
import { mergeZones } from '../scripts/generateZonesConfig.js';

const zonesGeo: WorldFeatureCollection = getJSON(
  path.resolve(fileURLToPath(new URL('world.geojson', import.meta.url)))
);

function generateBoundingBox(zoneKey: string) {
  const zonePath = path.resolve(
    fileURLToPath(new URL(`../../config/zones/${zoneKey}.yaml`, import.meta.url))
  );
  const zoneConfig = yaml.load(fs.readFileSync(zonePath, 'utf8')) as ZoneConfig;

  if (!zoneConfig) {
    console.error(`ERROR: Zone ${zoneKey} does not exist in configuration`);
    process.exit(1);
  }

  // do not modifiy current bounding boxes
  if (zoneConfig.bounding_box) {
    console.error(`Ignoring ${zoneKey} as it already have a bounding box`);
    return;
  }

  let zoneFeatures = zonesGeo.features.filter((d) => d.properties.zoneName === zoneKey);
  let isAggregate = false;
  if (zoneFeatures.length <= 0) {
    console.info(`Zone ${zoneKey} does not exist in geojson, using subzones instead`);
    isAggregate = true;
    zoneFeatures = zonesGeo.features.filter((d) => {
      return d.properties.countryKey === zoneKey;
    });
  }

  let allCoords: Position[] = [];
  let boundingBoxes: { [key: string]: number[][] } = {};

  for (const zone of zoneFeatures) {
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
    zoneConfig.bounding_box = [bbox[0], bbox[1]];

    saveZoneYaml(zoneKey, zoneConfig);
  }
}

function findZonesWithMissingBoundingBoxes(): string[] {
  const zoneConfig = mergeZones();
  const zonesWithMissingBoundingBoxes: string[] = [];
  for (const zoneKey of Object.keys(zoneConfig)) {
    if (!zoneConfig[zoneKey].bounding_box) {
      zonesWithMissingBoundingBoxes.push(zoneKey);
    }
  }
  return zonesWithMissingBoundingBoxes;
}

const inputArguments = process.argv.slice(2);

if (inputArguments.length <= 0) {
  console.error(
    'ERROR: Please add a zoneName parameter ("ts-node --esm generateZoneBoundingBoxes.ts DE" or use "ALL" to generate all missing bounding boxes)'
  );
  process.exit(1);
}

const zoneKey = inputArguments[0];

const zonesToCover = zoneKey === 'ALL' ? findZonesWithMissingBoundingBoxes() : [zoneKey];

// Ignore zones crossing the 180th meridian
const ignoredZones = new Set(['RU', 'RU', 'RU-FE', 'US-AK', 'US']);

for (const zoneKey of zonesToCover) {
  if (ignoredZones.has(zoneKey)) {
    console.log('Ignoring', zoneKey, 'because it is crossing the 180th meridian');
    continue;
  }

  generateBoundingBox(zoneKey);
  console.info(
    `Done, check /config/zones/${zoneKey}.yaml to verify that the result looks good!`
  );
}
