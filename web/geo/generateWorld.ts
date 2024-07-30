import * as path from 'node:path';
import { fileURLToPath } from 'node:url';

import { coordEach } from '@turf/turf';

import { getConfig } from '../scripts/generateZonesConfig.js';
import { generateAggregates } from './generateAggregates.js';
import { generateExchangesToIgnore } from './generateExchangesToExclude.js';
import { generateTopojson } from './generateTopojson.js';
import { WorldFeatureCollection } from './types.js';
import { getJSON, round } from './utilities.js';
import { validateGeometry } from './validate.js';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));

export const GEO_CONFIG = {
  WORLD_PATH: path.resolve(currentDirectory, 'world.geojson'),
  OUT_PATH: path.resolve(currentDirectory, '../config/world.json'),
  ERROR_PATH: path.resolve(currentDirectory, '.'),
  // TODO: The numbers here may not line up with the expected values in validateGeometry, as these numbers seem to be
  // somewhat arbitrarily picked to make the validation pass. We should probably revisit these numbers and see if they
  // can be improved.
  MIN_AREA_HOLES: 5_000_000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 6_000_000,
  SLIVER_RATIO: 0.0001, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
} as const;

const STATES_CONFIG = {
  STATES_PATH: path.resolve(currentDirectory, 'usa_states.geojson'),
  OUT_PATH: path.resolve(currentDirectory, '../config/usa_states.json'),
  ERROR_PATH: path.resolve(currentDirectory, '.'),
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
} as const;

const EXCHANGE_OUT_PATH = path.resolve(
  currentDirectory,
  '../config/excluded_aggregated_exchanges.json'
);

const worldFC: WorldFeatureCollection = getJSON(GEO_CONFIG.WORLD_PATH);
const statesFC: WorldFeatureCollection = getJSON(STATES_CONFIG.STATES_PATH);

const config = getConfig();
const aggregates = generateAggregates(worldFC, config.zones);

worldFC.features = aggregates;

// Rounds coordinates to 3 decimals
coordEach(worldFC, (coord) => {
  coord[0] = round(coord[0], 3);
  coord[1] = round(coord[1], 3);
});

const { skipped } = generateTopojson(worldFC, GEO_CONFIG);
const { skipped: statesSkipped } = generateTopojson(statesFC, STATES_CONFIG);

generateExchangesToIgnore(EXCHANGE_OUT_PATH, config.zones);

if (skipped === true) {
  console.info('No changes to world.json');
} else {
  validateGeometry(worldFC, GEO_CONFIG);
}

if (statesSkipped === true) {
  console.info('No changes to usa_states.json');
}
