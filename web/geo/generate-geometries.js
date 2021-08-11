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

console.log('generate-geometries: starting!');

const DIST_FOLDER = path.resolve(__dirname, '../public/dist');

const SRC_FOLDER = path.resolve(__dirname, '../src');

/**
 * Merges a list of GeoJSON Polygons or MultiPolygons into a single multi-polygon.
 * This allows to merge a group of geometries into a single one.
 * According to  "zoneDefinition" in "geometries-config.js", a single GeoJSON MultiPolygon is
 * created for each zone by grouping all geometries corresponding to that zone.
 */
function geomerge() {
  // Convert both into multipolygon
  const geos = Array.prototype.slice.call(arguments).filter((d) => d != null);
  geos.forEach((geo) => {
    if (geo.geometry.type === 'Polygon') {
      geo.geometry = {
        type: 'MultiPolygon',
        coordinates: [geo.geometry.coordinates],
      };
    } else if (geo.geometry.type !== 'MultiPolygon') {
      throw new Error(`Unexpected geometry type '${geo.geometry.type}'`);
    }
  });
  // Merge both
  return {
    type: 'Feature',
    geometry: {
      type: 'MultiPolygon',
      coordinates: Array.prototype.concat(...geos.map((d) => d.geometry.coordinates)),
    },
    properties: {},
  };
}

function hascMatch(properties, hasc) {
  return (
    properties.code_hasc === hasc ||
    (properties.hasc_maybe && properties.hasc_maybe.split('|').indexOf(hasc) !== -1)
  );
}

function equals(obj, prop, val) {
  return obj && prop in obj && obj[prop] === val;
}

function getCountry(countryId, geos) {
  return geomerge(...geos.filter((d) => equals(d, 'id', countryId)));
}
function getByPropertiesId(zoneId, geos) {
  return geomerge(...geos.filter((d) => equals(d.properties, 'id', zoneId)));
}
function getSubUnit(subid, geos) {
  return geomerge(...geos.filter((d) => equals(d.properties, 'subid', subid)));
}
function getState(countryId, geos, code_hasc, use_maybe = false) {
  return geomerge(
    ...geos.filter(
      (d) =>
        equals(d, 'id', countryId) &&
        'code_hasc' in d.properties &&
        ((use_maybe && hascMatch(d.properties, code_hasc)) || d.properties.code_hasc === code_hasc)
    )
  );
}
function getStateByFips(countryId, geos, fips) {
  return geomerge(
    ...geos.filter((d) => equals(d, 'id', countryId) && equals(d.properties, 'fips', fips))
  );
}
function getStateByAdm1(adm1_code, geos) {
  return geomerge(...geos.filter((d) => equals(d.properties, 'adm1_code', adm1_code)));
}
function getByRegionCod(region_cod, geos) {
  return geomerge(...geos.filter((d) => equals(d.properties, 'region_cod', region_cod)));
}
function getCounty(county_name, geos) {
  return geomerge(...geos.filter((d) => equals(d.properties, 'COUNTYNAME', county_name)));
}
function getStates(countryId, geos, code_hascs, use_maybe) {
  return geomerge(...code_hascs.map((d) => getState(countryId, geos, d, use_maybe)));
}
function getStatesByAdm1(adm1_codes, geos) {
  return geomerge(...adm1_codes.map((d) => getStateByAdm1(d, geos)));
}
function getCountries(countryIds, geos) {
  return geomerge(...countryIds.map((d) => getCountry(d, geos)));
}
function getSubUnits(ids, geos) {
  return geomerge(...ids.map((d) => getSubUnit(d, geos)));
}
function getCounties(names, geos) {
  return geomerge(...names.map((d) => getCounty(d, geos)));
}

const getDataForZone = (zone, geos, mergeStates) => {
  /* for a specifi zone, defined by an Object having at least `zoneName` and
   * `type` as properties, call the corresponding function to get the data */
  if (zone.type === 'country') {
    return getCountry(zone.id, geos);
  } else if (zone.type === 'states') {
    if (mergeStates) {
      return getStates(zone.countryId, geos, zone.states);
    } else {
      return ['multipleStates', zone.states.map((state) => getState(zone.countryId, geos, state))];
    }
  } else if (zone.type === 'state') {
    return getState(zone.countryId, geos, zone.stateId, zone.useMaybe);
  } else if (zone.type === 'administrations') {
    return getStatesByAdm1(zone.administrations, geos);
  } else if (zone.type === 'subunits') {
    return getSubUnits(zone.subunits, geos);
  } else if (zone.type === 'countries') {
    return getCountries(zone.countries, geos);
  } else if (zone.type === 'fips') {
    return getStateByFips(zone.fips[0], geos, zone.fips[1]);
  } else if (zone.type === 'subZone') {
    return getByPropertiesId(zone.id, geos);
  } else if (zone.type === 'region_cod') {
    if (typeof zone.region_cod === 'object') {
      // assume array
      return geomerge(...zone.region_cod.map((d) => getByRegionCod(d, geos)));
    } else {
      return getByRegionCod(zone.region_cod, geos);
    }
  } else if (zone.type === 'county') {
    return getCounties(zone.counties, geos);
  } else {
    console.warn(`unknown type "${zone.type}" for zone`, zone.zoneName);
  }
};

const toListOfFeatures = (zones) => {
  /* transform a list of (zoneName, properties) to the right geoJSON format */
  return zones
    .filter((d) => d[1] != null)
    .map((d) => {
      const [k, v] = d;
      const zoneName = k;
      v.id = zoneName;
      v.properties = {
        zoneName,
      };
      return v;
    });
};

/**
 * Adds the zones from topo2 to topo1.
 * Be aware that this function modifies the supplied variables!
*/
function mergeTopoJsonSingleZone(topo1, topo2) {
  const srcArcsLength = topo1.arcs.length;
  // Copy Zones from topo2 to topo1
  Object.keys(topo2.objects).forEach((zoneName) => {
    topo1.objects[zoneName] = topo2.objects[zoneName];
    // Relocate arc into zone by adding srcArcsLength
    topo1.objects[zoneName].arcs.forEach((arcList1) => {
      arcList1.forEach((arcList2) => {
        for (i = 0; i < arcList2.length; i++) {
          arcList2[i] += srcArcsLength;
        }
      });
    });
  });

  // Add arcs from topo2
  topo2.arcs.forEach((arc) => {
    topo1.arcs.push(arc);
  });
}

// create zones from definitions, avoid zones having moreDetails==true
function getZones(zoneDefinitions, geos) {
  const zones = {};
  zoneDefinitions.forEach((zone) => {
    if (zone.zoneName in zones)
      throw (
        `Warning: ${zone.zoneName} has duplicated entries. Each zoneName must be present ` +
        `only once in zoneDefinitions`
      );
    // Avoid zone with moreDetails
    if (!('moreDetails' in zone) || !zone.moreDetails) {
      zones[zone.zoneName] = getDataForZone(zone, geos, true);
    }
  });
  return zones;
}

function getZonesMoreDetails(zoneDefinitions, geos, zones) {
  // create zonesMoreDetails by getting zone having moreDetails===true
  const zonesMoreDetails = {};
  zoneDefinitions.forEach((zone) => {
    // Take only zones having modeDetails
    if ('moreDetails' in zone && zone.moreDetails) {
      if (zone.zoneName in zonesMoreDetails || zone.zoneName in zones)
        throw (
          `Warning: ${zone.zoneName} has duplicated entries. Each zoneName must be present ` +
          `only once in zoneDefinitions`
        );
      zonesMoreDetails[zone.zoneName] = getDataForZone(zone, geos, true);
    }
  });
  return zonesMoreDetails;
}

function getZoneFeatures(zoneDefinitions, geos) {
  // We do not want to merge states
  // related to PR #455 in the backend
  let zoneFeatures = zoneDefinitions.map((zone) => [
    zone.zoneName,
    getDataForZone(zone, geos, false),
  ]);
  // where there are multiple states, we need to inline the values
  const zoneFeaturesInline = [];
  zoneFeatures.forEach((data) => {
    const [name, zoneFeature] = data;
    if (Array.isArray(zoneFeature) && zoneFeature[0] === 'multipleStates') {
      zoneFeature[1].forEach((z) => {
        zoneFeaturesInline.push([name, z]);
      });
    } else {
      zoneFeaturesInline.push(data);
    }
  });
  zoneFeatures = toListOfFeatures(zoneFeaturesInline);
  return zoneFeatures;
}


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

fs.writeFileSync(`${SRC_FOLDER}/world.json`, JSON.stringify(mergedTopo));


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
