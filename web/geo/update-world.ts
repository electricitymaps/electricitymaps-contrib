// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'path'.
const path = require('path');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'validateGe... Remove this comment to see the full error message
const { validateGeometry } = require('./validate');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getJSON'.
const { getJSON } = require('./utilities');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'generateTo... Remove this comment to see the full error message
const { generateTopojson } = require('./generate-topojson');

const config = {
  // @ts-expect-error TS(2304): Cannot find name '__dirname'.
  WORLD_PATH: path.resolve(__dirname, './world.geojson'),
  // @ts-expect-error TS(2304): Cannot find name '__dirname'.
  OUT_PATH: path.resolve(__dirname, '../src/world.json'),
  // @ts-expect-error TS(2304): Cannot find name '__dirname'.
  ERROR_PATH: path.resolve(__dirname, '.'),
  MIN_AREA_HOLES: 600000000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 500000,
  SLIVER_RATIO: 0.01, // ratio of length and area to determine if the polygon is a sliver and should be ignored
  // @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const fc = getJSON(config.WORLD_PATH);
validateGeometry(fc, config);
generateTopojson(fc, config);
