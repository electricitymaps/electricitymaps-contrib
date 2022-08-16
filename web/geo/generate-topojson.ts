// @ts-expect-error TS(2580): Cannot find name 'require'. Do you need to install... Remove this comment to see the full error message
const { topology } = require('topojson-server');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getJSON'.
const { getJSON, writeJSON, round } = require('./utilities');
// @ts-expect-error TS(2580): Cannot find name 'require'. Do you need to install... Remove this comment to see the full error message
const turf = require('@turf/turf');

function getCenter(geojson: any, zoneName: any) {
  const geojsonFeatures = geojson.features.filter((f: any) => f.properties.zoneName === zoneName);
  if (geojsonFeatures.length !== 1) {
    console.error(`ERROR: Found ${geojsonFeatures.length} features matching zoneName ${zoneName}`);
    // @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
    process.exit(1);
  }

  const longitudes: any = [];
  const latitudes: any = [];

  turf.explode(geojsonFeatures[0].geometry).features.forEach(({ geometry }: any) => {
    const [longitude, latitude] = geometry.coordinates;
    longitudes.push(longitude);
    latitudes.push(latitude);
  });

  if (longitudes.length === 0 || latitudes.length === 0) {
    console.error(`ERROR: Found ${longitudes.length} longitudes and ${latitudes} latitudes for zoneName ${zoneName}`);
    // @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
    process.exit(1);
  }

  return [
    round((Math.min(...longitudes) + Math.max(...longitudes)) / 2, 1),
    round((Math.min(...latitudes) + Math.max(...latitudes)) / 2, 1),
  ];
}

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'generateTo... Remove this comment to see the full error message
function generateTopojson(fc: any, { OUT_PATH, verifyNoUpdates }: any) {
  console.log('Generating new world.json'); // eslint-disable-line no-console
  const topo = topology({
    objects: fc,
  });

  // We do the following to match the specific format needed for visualization
  const newObjects = {};
  topo.objects.objects.geometries.forEach((geo: any) => {
    // Precompute center for enable centering on the zone
    geo.properties.center = getCenter(fc, geo.properties.zoneName);

    // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
    newObjects[geo.properties.zoneName] = geo;
  });
  topo.objects = newObjects;

  const currentTopo = getJSON(OUT_PATH);
  if (JSON.stringify(currentTopo) === JSON.stringify(topo)) {
    console.log('No changes to world.json'); // eslint-disable-line no-console
    return;
  }

  if (verifyNoUpdates) {
    console.error('Did not expect any updates to world.json. Please run "yarn update-world"');
    // @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
    process.exit(1);
  }

  writeJSON(OUT_PATH, topo);
}

// @ts-expect-error TS(2580): Cannot find name 'module'. Do you need to install ... Remove this comment to see the full error message
module.exports = { generateTopojson };
