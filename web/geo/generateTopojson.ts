import * as turf from '@turf/turf';
import { topology } from 'topojson-server';
import { fileExists, getJSON, round, writeJSON } from './utilities.js';
import { WorldFeatureCollection } from './types.js';

function getCenter(geojson: WorldFeatureCollection, zoneName: string) {
  switch (zoneName) {
    case 'US-AK': {
      return [-151.77, 65.32];
    }
    case 'FJ': {
      return [178.09, -17.78];
    }
    case 'RU-FE': {
      return [171.57, 66.26];
    }
    default: {
      [0, 0];
    }
  }
  const geojsonFeatures = geojson.features.filter(
    (f) => f.properties.zoneName === zoneName
  );
  if (geojsonFeatures.length !== 1) {
    console.error(
      `ERROR: Found ${geojsonFeatures.length} features matching zoneName ${zoneName}`
    );
    process.exit(1);
  }

  const longitudes: number[] = [];
  const latitudes: number[] = [];

  for (const { geometry } of turf.explode(geojsonFeatures[0].geometry).features) {
    const [longitude, latitude] = geometry.coordinates;
    longitudes.push(longitude);
    latitudes.push(latitude);
  }

  if (longitudes.length === 0 || latitudes.length === 0) {
    console.error(
      `ERROR: Found ${longitudes.length} longitudes and ${latitudes} latitudes for zoneName ${zoneName}`
    );
    process.exit(1);
  }

  return [
    round((Math.min(...longitudes) + Math.max(...longitudes)) / 2, 1),
    round((Math.min(...latitudes) + Math.max(...latitudes)) / 2, 1),
  ];
}

function generateTopojson(
  fc: WorldFeatureCollection,
  { OUT_PATH, verifyNoUpdates }: { OUT_PATH: string; verifyNoUpdates: boolean }
) {
  const output = OUT_PATH.split('/').pop();
  console.info(`Generating new ${output}`);
  const topo = topology({
    objects: fc,
  });

  // We do the following to match the specific format needed for visualization
  const objects = topo.objects.objects as any;
  const newObjects = {} as typeof topo.objects;
  for (const geo of objects.geometries) {
    // Precompute center for enable centering on the zone
    geo.properties.center = getCenter(fc, geo.properties.zoneName);

    newObjects[geo.properties.zoneName] = geo;
  }
  topo.objects = newObjects;

  const currentTopo = fileExists(OUT_PATH) ? getJSON(OUT_PATH) : {};
  if (JSON.stringify(currentTopo) === JSON.stringify(topo)) {
    console.info(`No changes to ${output}`);
    return { skipped: true };
  }

  if (verifyNoUpdates) {
    console.error(
      'Did not expect any updates to world.json. Please run "pnpm generate-world"'
    );
    process.exit(1);
  }

  writeJSON(OUT_PATH, topo);
  return { skipped: false };
}

export { generateTopojson };
