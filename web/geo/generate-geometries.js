const fs = require('fs');
const path = require('path');
const topojson = require('topojson');

const {
  countryGeos,
  stateGeos,
  thirdpartyGeos,
  USOriginalGeos,
  USSimplifiedGeos,
  zoneDefinitions,
} = require('./geometries-config');
const {
  getZones,
  getZonesMoreDetails,
  getZoneFeatures,
  mergeTopoJsonSingleZone,
} = require('./utils');

console.log('generate-geometries: starting!');

const DIST_FOLDER = path.resolve(__dirname, '../public/dist');
const SRC_FOLDER = path.resolve(__dirname, '../src');

/**
 * Shrinks the topojson file by simplifiying the polygons.
 * @param {Object} baseTopo - TopoJSON object
 * @param {Object} baseTopoDetails - TopoJSON object
 * @returns {Object} - TopoJSON object
 */
function shrinkAndMergeTopoJson(baseTopo, baseTopoDetails) {
  let topo = baseTopo;
  let topoMoreDetails = baseTopoDetails;

  // Simplify all countries
  topo = topojson.presimplify(topo);
  topo = topojson.simplify(topo, 0.01);
  topo = topojson.filter(topo, topojson.filterWeight(topo, 0.009));

  // Simplify to 0.001 zonesMoreDetails zones
  topoMoreDetails = topojson.presimplify(topoMoreDetails);
  topoMoreDetails = topojson.simplify(topoMoreDetails, 0.001);

  // Merge topoMoreDetails into topo
  mergeTopoJsonSingleZone(topo, topoMoreDetails);

  topo = topojson.quantize(topo, 1e5);

  return topo;
}

// The following data includes simplified shapes and should only be used for display zones on the map
const webGeos = countryGeos.concat(stateGeos, thirdpartyGeos, USSimplifiedGeos);
const zones = getZones(zoneDefinitions, webGeos);
const zonesMoreDetails = getZonesMoreDetails(zoneDefinitions, webGeos, zones);

// Convert from GeoJSON to TopoJSON which is a more compressed format than geoJSON.
// It only stores arcs that are used multiple times once.
const topo = topojson.topology(zones);
const topoDetails = topojson.topology(zonesMoreDetails);
const mergedTopo = shrinkAndMergeTopoJson(topo, topoDetails);

// If script was called with argument '--ignore-world', let's not write the file to disk
if (process.argv[2] === '--ignore-world') {
  console.log('Skipping creation of world.json due to flag');
} else {
  fs.writeFileSync(`${SRC_FOLDER}/world.json`, JSON.stringify(mergedTopo));
}

// The following data includes complex shapes and should only be used in the backend to query by lon/lat
const backendGeos = countryGeos.concat(stateGeos, thirdpartyGeos, USOriginalGeos);
const backendZoneFeatures = getZoneFeatures(zoneDefinitions, backendGeos);

if (!fs.existsSync(DIST_FOLDER)) {
  fs.mkdirSync(DIST_FOLDER);
}

// Write unsimplified list of geojson, without state merges including overlapping US zones
fs.writeFileSync(
  `${DIST_FOLDER}/zonegeometries.json`,
  backendZoneFeatures.map(JSON.stringify).join('\n')
);

console.log('generate-geometries: done!');
