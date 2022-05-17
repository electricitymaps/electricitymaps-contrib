const {
  area,
  bbox,
  bboxPolygon,
  convex,
  dissolve,
  featureCollection,
  featureEach,
  getGeom,
  intersect,
} = require('@turf/turf');
const { getPolygons, getHoles, writeJSON, log } = require('./utilities');

const { getZonesJson } = require('./files');

// TODO: Improve this function so each check returns error messages,
// so we can show all errors instead of taking them one at a time.
function validateGeometry(fc, config) {
  console.log('Validating geometries...'); // eslint-disable-line no-console
  zeroNullGeometries(fc);
  containsRequiredProperties(fc);
  zeroComplexPolygons(fc, config);
  zeroNeighboringIds(fc);
  zeroGaps(fc, config);
  zeroOverlaps(fc, config);
  matchesZonesConfig(fc, config);
}

function zeroNullGeometries(fc) {
  const nullGeometries = fc.features
    .filter((ft) => !getGeom(ft).coordinates.length)
    .map((ft) => ft.properties.zoneName);
  if (nullGeometries.length) {
    nullGeometries.forEach((zoneName) => log(`${zoneName} has null geometry`));
    throw Error('Feature(s) contains null geometry');
  }
}

function containsRequiredProperties(fc) {
  const indexes = getPolygons(fc)
    .features.map(({ properties }, idx) =>
      properties.zoneName || properties.countryKey || properties.countryName ? null : idx
    )
    .filter((x) => x);

  if (indexes.length) {
    indexes.forEach((x) => log(`feature (idx ${x}) missing properties`));
    throw Error('Feature(s) are missing properties');
  }
}

function zeroComplexPolygons(fc, { MAX_CONVEX_DEVIATION }) {
  // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
  // calculate deviation from the convex hull and returns array of polygons with high complexity

  const zoneNames = getPolygons(fc)
    .features.map((ft) => {
      try {
        const deviation = (area(convex(ft)) - area(ft)) / area(convex(ft));
        return { deviation, zoneName: ft.properties.zoneName };
      } catch (error) {
        // assumes the feature is complex
        log(`${ft.properties.zoneName} cannot calculate complexity`);
        console.error(error);
        return { deviation: Number.MAX_SAFE_INTEGER, zoneName: ft.properties.zoneName };
      }
    })
    .filter((x) => x.deviation > MAX_CONVEX_DEVIATION)
    .map((x) => x.zoneName);

  if (zoneNames.length) {
    zoneNames.forEach((x) => log(`${x} is too complex`));
    throw Error('Feature(s) too complex');
  }
}

function matchesZonesConfig(fc) {
  const zonesJson = getZonesJson();

  const missingZones = [];
  featureEach(fc, (ft) => {
    if (!(ft.properties.zoneName in zonesJson)) {
      missingZones.push(ft.properties.zoneName);
    }
  });
  if (missingZones.length) {
    missingZones.forEach((x) => log(`${x} not in zones.json`));
    throw Error('Zonename not in zones.json');
  }
}

function zeroGaps(fc, { ERROR_PATH, MIN_AREA_HOLES }) {
  const dissolved = getPolygons(dissolve(getPolygons(fc)));
  const holes = getHoles(dissolved, MIN_AREA_HOLES);

  if (holes.features.length > 0) {
    writeJSON(`${ERROR_PATH}/gaps.geojson`, holes);
    holes.features.forEach((_) => log(`Found gap, see gaps.geojson`));
    throw Error('Contains gaps');
  }
}

function zeroNeighboringIds(fc) {
  // Throws error if multiple polygons have the same zoneName and are right next to each other,
  // in that case they should be merged as one polygon

  const groupedByZoneNames = getPolygons(fc).features.reduce((acc, cval) => {
    const { zoneName } = cval.properties;
    if (acc[zoneName]) {
      acc[zoneName].push(cval);
    } else {
      acc[zoneName] = [cval];
    }
    return acc;
  }, {});

  // dissolve each group, if length decreases, it means that they are superfluous neigbors
  const zoneNames = Object.entries(groupedByZoneNames)
    .map(([zoneId, polygons]) => {
      const dissolved = dissolve(featureCollection(polygons));
      return dissolved.features.length < polygons.length ? zoneId : null;
    })
    .filter((x) => x);

  if (zoneNames.length) {
    zoneNames.forEach((x) => log(`${x} has neighbor with identical ID`));
    throw Error('Contains neighboring id zone');
  }
}

function zeroOverlaps(fc, { MIN_AREA_INTERSECTION }) {
  // add bbox to features to increase speed
  const features = getPolygons(fc).features.map((ft) => ({ ft, bbox: bboxPolygon(bbox(ft)) }));

  const overlaps = features
    .filter(
      (ft1, idx1) =>
        features.filter((ft2, idx2) => {
          if (idx1 !== idx2 && intersect(ft1.bbox, ft2.bbox)) {
            const intersection = intersect(ft1.ft, ft2.ft);
            if (intersection && area(intersection) > MIN_AREA_INTERSECTION) {
              return true;
            }
          }
        }).length
    )
    .map(({ ft, _ }) => ft.properties.zoneName);

  if (overlaps.length) {
    overlaps.forEach((x) => console.error(`${x} overlaps with another feature`));
    throw Error('Feature(s) overlap');
  }
}

module.exports = { validateGeometry };
