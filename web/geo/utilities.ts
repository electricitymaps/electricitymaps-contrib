const {
  polygon,
  getCoords,
  getType,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'featureEac... Remove this comment to see the full error message
  featureEach,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'featureCol... Remove this comment to see the full error message
  featureCollection,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'area'.
  area,
  truncate,
  polygonToLineString,
  // @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'length'.
  length,
  // @ts-expect-error TS(2580): Cannot find name 'require'. Do you need to install... Remove this comment to see the full error message
} = require('@turf/turf');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'fs'.
const fs = require('fs');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getPolygon... Remove this comment to see the full error message
function getPolygons(input: any) {
  /* Transform the feature collection of polygons and multi-polygons into a feature collection of polygons only */
  /* all helper functions should rely on its output */
  const handlePolygon = (feature: any, props: any) => polygon(getCoords(feature), props);
  const handleMultiPolygon = (feature: any, props: any) =>
    getCoords(feature).map((coord: any) => polygon(coord, props));

  const polygons: any = [];
  let fc;
  if (getType(input) !== 'FeatureCollection') {
    fc = featureCollection([input]);
  } else {
    fc = input;
  }

  featureEach(fc, (feature: any) => {
    const type = getType(feature);
    switch (type) {
      case 'Polygon':
        polygons.push(handlePolygon(feature, feature.properties));
        break;
      case 'MultiPolygon':
        polygons.push(...handleMultiPolygon(feature, feature.properties));
        break;
      default:
        throw Error(`Encountered unhandled type: ${type}`);
    }
  });

  return truncate(featureCollection(polygons), { precision: 6 });
}

function isSliver(polygon: any, polArea: any, sliverRatio: any) {
  // @ts-expect-error TS(2349): This expression is not callable.
  const lineStringLength = length(polygonToLineString(polygon));
  return lineStringLength / polArea < sliverRatio;
}

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getHoles'.
function getHoles(fc: any, minArea: any, sliverRatio: any) {
  const holes: any = [];
  featureEach(fc, (ft: any) => {
    const coords = getCoords(ft);
    if (coords.length > 1) {
      for (let i = 1; i < coords.length; i++) {
        const pol = polygon([coords[i]]);
        const polArea = area(pol);
        if (polArea < minArea && !isSliver(pol, polArea, sliverRatio)) {
          holes.push(pol);
        }
      }
    }
  });
  return featureCollection(holes);
}

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getJSON'.
const getJSON = (fileName: any, encoding = 'utf8') => JSON.parse(fs.readFileSync(fileName, encoding));

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'writeJSON'... Remove this comment to see the full error message
const writeJSON = (fileName: any, obj: any, encoding = 'utf8') =>
  fs.writeFileSync(fileName, JSON.stringify(obj), encoding);

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'log'.
function log(message: any) {
  console.error('\x1b[31m%s\x1b[0m', `ERROR: ${message}`);
}

/**
 * Function to round a number to a specific amount of decimals.
 * @param {number} number - The number to round.
 * @param {number} decimals - Defaults to 2 decimals.
 * @returns {number} Rounded number.
 */
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'round'.
const round = (number: any, decimals = 2) => {
  return Math.round((number + Number.EPSILON) * 10 ** decimals) / 10 ** decimals;
};

// @ts-expect-error TS(2580): Cannot find name 'module'. Do you need to install ... Remove this comment to see the full error message
module.exports = { getPolygons, getHoles, writeJSON, getJSON, log, round };
