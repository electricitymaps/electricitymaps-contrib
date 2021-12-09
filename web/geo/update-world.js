const { validateGeometry } = require('./validate');
const { detectChanges } = require('./detect-changes');
const { getJSON } = require('./utilities');
const { generateTopojson } = require('./generate-topojson');

const config = {
  WORLD_PATH: './geo/world.geojson',
  OUT_PATH: './src/world.json',
  ERROR_PATH: './geo',
  MIN_AREA_HOLES: 600000000,
  MAX_CONVEX_DEVIATION: 0.708,
  MIN_AREA_INTERSECTION: 500000
};

const fc = getJSON(config.WORLD_PATH);
validateGeometry(fc, config);
detectChanges(fc, config);
generateTopojson(fc, config);