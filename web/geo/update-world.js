const path = require('path');
const { validateGeometry } = require('./validate');
const { getJSON, roundGeoPoints } = require('./utilities');
const { generateTopojson } = require('./generate-topojson');
const { generateAggregates } = require('./generate-aggregates');
const { generateExchangesToIgnore } = require('./generate-exchanges-to-exclude');
const { mergeZones } = require('../generate-zones-config');

const config = {
  WORLD_PATH: path.resolve(__dirname, './world.geojson'),
  OUT_PATH: path.resolve(__dirname, '../src/config/world.json'),
  ERROR_PATH: path.resolve(__dirname, '.'),
  MIN_AREA_HOLES: 5000000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 6000000,
  SLIVER_RATIO: 0.0001, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const EXCHANGE_OUT_PATH = path.resolve(__dirname, '../src/config/excluded-aggregated-exchanges.json');

const fc = roundGeoPoints(getJSON(config.WORLD_PATH));
const zoneConfig = mergeZones();
const aggregates = generateAggregates(fc, zoneConfig);

fc.features = aggregates;

validateGeometry(fc, config);
generateTopojson(fc, config);
generateExchangesToIgnore(EXCHANGE_OUT_PATH, zoneConfig);
