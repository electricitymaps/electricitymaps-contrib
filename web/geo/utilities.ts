import {
  area,
  Feature,
  featureCollection,
  FeatureCollection,
  featureEach,
  MultiPolygon,
  getCoords,
  getType,
  length,
  Polygon,
  polygon,
  polygonToLineString,
  Properties,
  truncate,
} from '@turf/turf';
import * as fs from 'node:fs';

/* Transform the feature collection of polygons and multi-polygons into a feature collection of polygons only */
/* all helper functions should rely on its output */
const handlePolygon = (feature: Feature<Polygon, Properties>) =>
  polygon(getCoords(feature), feature.properties);

const handleMultiPolygon = (feature: Feature<MultiPolygon, Properties>) =>
  getCoords(feature).map((coord) => polygon(coord, feature.properties));

function getPolygons(fc: FeatureCollection<Polygon | MultiPolygon, Properties>) {
  const polygons: Feature<Polygon, Properties>[] = [];

  featureEach(fc, (feature) => {
    const type = getType(feature);
    switch (type) {
      case 'Polygon': {
        polygons.push(handlePolygon(feature as Feature<Polygon, Properties>));
        break;
      }
      case 'MultiPolygon': {
        polygons.push(
          ...handleMultiPolygon(feature as Feature<MultiPolygon, Properties>)
        );
        break;
      }
      default: {
        throw new Error(`Encountered unhandled type: ${type}`);
      }
    }
  });

  return truncate(featureCollection(polygons), { precision: 6 });
}

function isSliver(
  polygon: Feature<Polygon, Properties>,
  polArea: number,
  sliverRatio: number
) {
  const lineStringLength = length(polygonToLineString(polygon));
  return Number(lineStringLength / polArea) > Number(sliverRatio);
}

function getHoles(
  fc: FeatureCollection<Polygon | MultiPolygon, Properties>,
  minArea: number,
  sliverRatio: number
) {
  const holes: Feature<Polygon, Properties>[] = [];
  featureEach(fc, (feature: Feature<Polygon | MultiPolygon, Properties>) => {
    const coords = getCoords(feature);
    if (coords.length > 0) {
      for (const coord of coords) {
        const pol = polygon([coord]);
        const polArea = area(pol);
        if (polArea < minArea && !isSliver(pol, polArea, sliverRatio)) {
          holes.push(pol);
        }
      }
    }
  });
  return featureCollection(holes);
}

const fileExists = (fileName: string) => fs.existsSync(fileName);

const getJSON = (fileName: string) => JSON.parse(fs.readFileSync(fileName, 'utf8'));

const writeJSON = (fileName: string, object: unknown) =>
  fs.writeFileSync(fileName, JSON.stringify(object), { encoding: 'utf8', flag: 'w' });

function log(message: string) {
  console.error('\u001B[31m%s\u001B[0m', `ERROR: ${message}`);
}

/**
 * Function to round a number to a specific amount of decimals.
 * @param {number} number - The number to round.
 * @param {number} decimals - Defaults to 2 decimals.
 * @returns {number} Rounded number.
 */
const round = (number: number, decimals = 2): number =>
  Math.round((number + Number.EPSILON) * 10 ** decimals) / 10 ** decimals;

export { getPolygons, getHoles, isSliver, writeJSON, getJSON, log, round, fileExists };
