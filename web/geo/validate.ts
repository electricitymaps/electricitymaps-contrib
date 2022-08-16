/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-var-requires */
const {
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'area'.
  area,
  bbox,
  bboxPolygon,
  convex,
  dissolve,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'featureCol... Remove this comment to see the full error message
  featureCollection,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'featureEac... Remove this comment to see the full error message
  featureEach,
  getGeom,
  intersect,
  // @ts-expect-error TS(2580): Cannot find name 'require'. Do you need to install... Remove this comment to see the full error message
} = require('@turf/turf');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getPolygon... Remove this comment to see the full error message
const { getPolygons, getHoles, writeJSON, log } = require('./utilities');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getZonesJs... Remove this comment to see the full error message
const { getZonesJson } = require('./files');

// TODO: Improve this function so each check returns error messages,
// so we can show all errors instead of taking them one at a time.
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'validateGe... Remove this comment to see the full error message
function validateGeometry(fc: any, config: any) {
  console.log('Validating geometries...'); // eslint-disable-line no-console
  zeroNullGeometries(fc);
  containsRequiredProperties(fc);
  zeroComplexPolygons(fc, config);
  zeroNeighboringIds(fc);
  zeroGaps(fc, config);
  zeroOverlaps(fc, config);
  // @ts-expect-error TS(2554): Expected 1 arguments, but got 2.
  matchesZonesConfig(fc, config);
}

function zeroNullGeometries(fc: any) {
  const nullGeometries = fc.features
    .filter((ft: any) => !getGeom(ft).coordinates.length)
    .map((ft: any) => ft.properties.zoneName);
  if (nullGeometries.length) {
    nullGeometries.forEach((zoneName: any) => log(`${zoneName} has null geometry`));
    throw Error('Feature(s) contains null geometry');
  }
}

function containsRequiredProperties(fc: any) {
  const indexes = getPolygons(fc)
    .features.map(({ properties }: any, idx: any) =>
      properties.zoneName || properties.countryKey || properties.countryName ? null : idx
    )
    .filter((x: any) => x);

  if (indexes.length) {
    indexes.forEach((x: any) => log(`feature (idx ${x}) missing properties`));
    throw Error('Feature(s) are missing properties');
  }
}

function zeroComplexPolygons(fc: any, { MAX_CONVEX_DEVIATION }: any) {
  // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
  // calculate deviation from the convex hull and returns array of polygons with high complexity

  const zoneNames = getPolygons(fc)
    .features.map((ft: any) => {
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
    .filter((x: any) => x.deviation > MAX_CONVEX_DEVIATION)
    .map((x: any) => x.zoneName);

  if (zoneNames.length) {
    zoneNames.forEach((x: any) => log(`${x} is too complex`));
    throw Error('Feature(s) too complex');
  }
}

function matchesZonesConfig(fc: any) {
  const zonesJson = getZonesJson();

  const missingZones: any = [];
  featureEach(fc, (ft: any) => {
    if (!(ft.properties.zoneName in zonesJson)) {
      missingZones.push(ft.properties.zoneName);
    }
  });
  if (missingZones.length) {
    // @ts-expect-error TS(7006): Parameter 'x' implicitly has an 'any' type.
    missingZones.forEach((x) => log(`${x} not in zones.json`));
    throw Error('Zonename not in zones.json');
  }
}

function zeroGaps(fc: any, { ERROR_PATH, MIN_AREA_HOLES, SLIVER_RATIO }: any) {
  const dissolved = getPolygons(dissolve(getPolygons(fc)));
  const holes = getHoles(dissolved, MIN_AREA_HOLES, SLIVER_RATIO);

  if (holes.features.length > 0) {
    writeJSON(`${ERROR_PATH}/gaps.geojson`, holes);
    holes.features.forEach((_: any) => log(`Found gap, see gaps.geojson`));
    throw Error('Contains gaps');
  }
}

function zeroNeighboringIds(fc: any) {
  // Throws error if multiple polygons have the same zoneName and are right next to each other,
  // in that case they should be merged as one polygon

  const groupedByZoneNames = getPolygons(fc).features.reduce((acc: any, cval: any) => {
    const { zoneName } = cval.properties;
    if (acc[zoneName]) {
      acc[zoneName].push(cval);
    } else {
      acc[zoneName] = [cval];
    }
    return acc;
  }, {});

  // dissolve each group, if length decreases, it means that they are superfluous neigbors
  // @ts-expect-error TS(2550): Property 'entries' does not exist on type 'ObjectC... Remove this comment to see the full error message
  const zoneNames = Object.entries(groupedByZoneNames)
    // @ts-expect-error TS(7031): Binding element 'zoneId' implicitly has an 'any' t... Remove this comment to see the full error message
    .map(([zoneId, polygons]) => {
      const dissolved = dissolve(featureCollection(polygons));
      return dissolved.features.length < polygons.length ? zoneId : null;
    })
    .filter((x: any) => x);

  if (zoneNames.length) {
    zoneNames.forEach((x: any) => log(`${x} has neighbor with identical ID`));
    throw Error('Contains neighboring id zone');
  }
}

function zeroOverlaps(fc: any, { MIN_AREA_INTERSECTION }: any) {
  // add bbox to features to increase speed
  const features = getPolygons(fc).features.map((ft: any) => ({
    ft,
    bbox: bboxPolygon(bbox(ft)),
  }));

  const overlaps = features
    .filter(
      (ft1: any, idx1: any) =>
        features.filter((ft2: any, idx2: any) => {
          if (idx1 !== idx2 && intersect(ft1.bbox, ft2.bbox)) {
            const intersection = intersect(ft1.ft, ft2.ft);
            if (intersection && area(intersection) > MIN_AREA_INTERSECTION) {
              return true;
            }
          }
        }).length
    )
    .map(({ ft, _ }: any) => ft.properties.zoneName);

  if (overlaps.length) {
    overlaps.forEach((x: any) => console.error(`${x} overlaps with another feature`));
    throw Error('Feature(s) overlap');
  }
}

// @ts-expect-error TS(2580): Cannot find name 'module'. Do you need to install ... Remove this comment to see the full error message
module.exports = { validateGeometry };
