/* eslint-disable @typescript-eslint/no-var-requires */
const path = require('path');

const { validateGeometry } = require('./validate');
const { getJSON } = require('./utilities');
const { generateTopojson } = require('./generate-topojson');

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

const fc = getJSON(config.WORLD_PATH);
validateGeometry(fc, config);
generateTopojson(fc, config);
