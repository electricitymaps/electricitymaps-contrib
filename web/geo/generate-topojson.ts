const { topology } = require('topojson-server');
const { getJSON, writeJSON, round } = require('./utilities');
const turf = require('@turf/turf');

function getCenter(geojson, zoneName) {
  const geojsonFeatures = geojson.features.filter((f) => f.properties.zoneName === zoneName);
  if (geojsonFeatures.length !== 1) {
    console.error(`ERROR: Found ${geojsonFeatures.length} features matching zoneName ${zoneName}`);
    process.exit(1);
  }

  const longitudes = [];
  const latitudes = [];

  turf.explode(geojsonFeatures[0].geometry).features.forEach(({ geometry }) => {
    const [longitude, latitude] = geometry.coordinates;
    longitudes.push(longitude);
    latitudes.push(latitude);
  });

  if (longitudes.length === 0 || latitudes.length === 0) {
    console.error(`ERROR: Found ${longitudes.length} longitudes and ${latitudes} latitudes for zoneName ${zoneName}`);
    process.exit(1);
  }

  return [
    round((Math.min(...longitudes) + Math.max(...longitudes)) / 2, 1),
    round((Math.min(...latitudes) + Math.max(...latitudes)) / 2, 1),
  ];
}

function generateTopojson(fc, { OUT_PATH, verifyNoUpdates }) {
  console.log('Generating new world.json'); // eslint-disable-line no-console
  const topo = topology({
    objects: fc,
  });

  // We do the following to match the specific format needed for visualization
  const newObjects = {};
  topo.objects.objects.geometries.forEach((geo) => {
    // Precompute center for enable centering on the zone
    geo.properties.center = getCenter(fc, geo.properties.zoneName);

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
    process.exit(1);
  }

  writeJSON(OUT_PATH, topo);
}

module.exports = { generateTopojson };
