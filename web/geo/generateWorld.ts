import { coordEach } from '@turf/turf';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mergeZones } from '../scripts/generateZonesConfig.js';
import { generateAggregates } from './generateAggregates.js';
import { generateExchangesToIgnore } from './generateExchangesToExclude.js';
import { generateTopojson } from './generateTopojson.js';
import { getJSON, round } from './utilities.js';
import { validateGeometry } from './validate.js';
import { WorldFeatureCollection } from './types.js';

export const config = {
  WORLD_PATH: path.resolve(fileURLToPath(new URL('world.geojson', import.meta.url))),
  OUT_PATH: path.resolve(fileURLToPath(new URL('../config/world.json', import.meta.url))),
  ERROR_PATH: path.resolve(fileURLToPath(new URL('.', import.meta.url))),
  MIN_AREA_HOLES: 5_000_000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 6_000_000,
  SLIVER_RATIO: 0.0001, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
} as const;

const EXCHANGE_OUT_PATH = path.resolve(
  fileURLToPath(new URL('../config/excludedAggregatedExchanges.json', import.meta.url))
);

const fc: WorldFeatureCollection = getJSON(config.WORLD_PATH);
const zoneConfig = mergeZones();
const aggregates = generateAggregates(fc, zoneConfig);

fc.features = aggregates;

// Rounds coordinates to 4 decimals
coordEach(fc, (coord) => {
  coord[0] = round(coord[0], 4);
  coord[1] = round(coord[1], 4);
});

const { skipped } = generateTopojson(fc, config);

generateExchangesToIgnore(EXCHANGE_OUT_PATH, zoneConfig);

if (skipped === true) {
  console.info('No changes to world.json');
} else {
  validateGeometry(fc, config);
}
