import * as path from 'node:path';
import { mergeZones } from '../generate-zones-config';
import { generateAggregates } from './generate-aggregates';
import { generateExchangesToIgnore } from './generate-exchanges-to-exclude';
import { generateTopojson } from './generate-topojson';
import { getJSON } from './utilities';
import { validateGeometry } from './validate';

const config = {
  WORLD_PATH: path.resolve(__dirname, './world.geojson'),
  OUT_PATH: path.resolve(__dirname, '../src/config/world.json'),
  ERROR_PATH: path.resolve(__dirname, '.'),
  MIN_AREA_HOLES: 5_000_000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 6_000_000,
  SLIVER_RATIO: 0.0001, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const EXCHANGE_OUT_PATH = path.resolve(
  __dirname,
  '../src/config/excluded-aggregated-exchanges.json'
);

const fc = getJSON(config.WORLD_PATH);
const zoneConfig = mergeZones();
const aggregates = generateAggregates(fc, zoneConfig);

fc.features = aggregates;

validateGeometry(fc, config);
generateTopojson(fc, config);
generateExchangesToIgnore(EXCHANGE_OUT_PATH, zoneConfig);
