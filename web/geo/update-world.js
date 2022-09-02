const path = require('path');

const { validateGeometry } = require('./validate');
const { validateGeometryV2 } = require('./validate-v2');
const { getJSON } = require('./utilities');
const { generateTopojson } = require('./generate-topojson');
const { generateAggregates } = require('./generate-aggregates');
const { generateExchangesToIgnore } = require('./generate-exchanges-to-exclude');
const { getZonesJson } = require('./files');

const config = {
  WORLD_PATH: path.resolve(__dirname, './world.geojson'),
  OUT_PATH: path.resolve(__dirname, '../src/world.json'),
  ERROR_PATH: path.resolve(__dirname, '.'),
  MIN_AREA_HOLES: 600000000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 500000,
  SLIVER_RATIO: 0.01, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};
const configV2 = {
  WORLD_PATH: path.resolve(__dirname, './world.geojson'),
  OUT_PATH: path.resolve(__dirname, '../src/world-aggregated.json'),
  ERROR_PATH: path.resolve(__dirname, '.'),
  MIN_AREA_HOLES: 600000000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 600000,
  SLIVER_RATIO: 1, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const EXCHANGE_OUT_PATH = path.resolve(__dirname, '../src/excluded-aggregated-exchanges.json');

const fc = getJSON(config.WORLD_PATH);
validateGeometry(fc, config);
generateTopojson(fc, config);

const fcV2 = getJSON(config.WORLD_PATH);
const zoneConfig = getZonesJson();
const aggregates = generateAggregates(fcV2, zoneConfig);

fcV2.features = aggregates;

validateGeometryV2(fcV2, configV2);
generateTopojson(fcV2, configV2);
generateExchangesToIgnore(EXCHANGE_OUT_PATH, fcV2);
