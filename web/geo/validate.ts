import {
  Feature,
  Polygon,
  area,
  bbox,
  bboxPolygon,
  convex,
  dissolve,
  featureCollection,
  featureEach,
  getGeom,
  intersect,
} from '@turf/turf';
import { getHoles, getPolygons, log, writeJSON } from './utilities.js';

import { mergeZones } from '../scripts/generateZonesConfig.js';
import { GeoConfig, WorldFeatureCollection } from './types.js';

// TODO: Improve this function so each check returns error messages,
// so we can show all errors instead of taking them one at a time.
function validateGeometry(fc: WorldFeatureCollection, config: GeoConfig) {
  console.info('Validating geometries...');
  zeroNullGeometries(fc);
  containsRequiredProperties(fc);
  zeroComplexPolygons(fc, config);
  zeroNeighboringIds(fc);
  zeroGaps(fc, config);
  zeroOverlaps(fc, config);
  matchesZonesConfig(fc);
}

function zeroNullGeometries(fc: WorldFeatureCollection) {
  const nullGeometries = fc.features
    .filter((ft) => getGeom(ft).coordinates.length === 0)
    .map((ft) => ft.properties.zoneName);
  if (nullGeometries.length > 0) {
    for (const zoneName of nullGeometries) {
      log(`${zoneName} has null geometry`);
    }
    throw new Error('Feature(s) contains null geometry');
  }
}

function containsRequiredProperties(fc: WorldFeatureCollection) {
  const indexes = getPolygons(fc)
    .features.map(({ properties }, index) =>
      properties?.zoneName || properties?.countryKey || properties?.countryName
        ? null
        : index
    )
    .filter(Boolean);

  if (indexes.length > 0) {
    for (const x of indexes) {
      log(`feature (idx ${x}) missing properties`);
    }
    throw new Error('Feature(s) are missing properties');
  }
}

function zeroComplexPolygons(
  fc: WorldFeatureCollection,
  { MAX_CONVEX_DEVIATION }: GeoConfig
) {
  // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
  // calculate deviation from the convex hull and returns array of polygons with high complexity

  const zoneNames = getPolygons(fc)
    .features.map((ft) => {
      try {
        const convexFeature = convex(ft);
        if (convexFeature === null) {
          throw new Error("Can't calculate convex hull");
        }
        const deviation = (area(convexFeature) - area(ft)) / area(convexFeature);
        return { deviation, zoneName: ft.properties?.zoneName };
      } catch (error) {
        // assumes the feature is complex
        log(`${ft.properties?.zoneName} cannot calculate complexity`);
        console.error(error);
        return { deviation: Number.MAX_SAFE_INTEGER, zoneName: ft.properties?.zoneName };
      }
    })
    .filter((x) => x.deviation > MAX_CONVEX_DEVIATION)
    .map((x) => x.zoneName);

  if (zoneNames.length > 0) {
    for (const x of zoneNames) {
      log(`${x} is too complex`);
    }
    throw new Error('Feature(s) too complex');
  }
}

function matchesZonesConfig(fc: WorldFeatureCollection) {
  const zonesJson = mergeZones();

  const missingZones: string[] = [];
  featureEach(fc, (ft) => {
    if (!(ft.properties?.zoneName in zonesJson)) {
      missingZones.push(ft.properties?.zoneName);
    }
  });
  if (missingZones.length > 0) {
    for (const x of missingZones) {
      log(`${x} not in zones/*.yaml`);
    }
    throw new Error('Zonename not in zones/*.yaml');
  }
}

function zeroGaps(
  fc: WorldFeatureCollection,
  { ERROR_PATH, MIN_AREA_HOLES, SLIVER_RATIO }: GeoConfig
) {
  const dissolved = getPolygons(dissolve(getPolygons(fc)));
  const holes = getHoles(dissolved, MIN_AREA_HOLES, SLIVER_RATIO);

  if (holes.features.length > 0) {
    writeJSON(`${ERROR_PATH}/gaps.geojson`, holes);
    for (const _ of holes.features) {
      log(`Found gap, see gaps.geojson`);
    }
    throw new Error('Contains gaps');
  }
}

function zeroNeighboringIds(fc: WorldFeatureCollection) {
  // Throws error if multiple polygons have the same zoneName and are right next to each other,
  // in that case they should be merged as one polygon
  const groupedByZoneNames = getPolygons(fc).features.reduce((accumulator, cval) => {
    const zoneName = cval.properties?.zoneName;
    if (accumulator[zoneName]) {
      accumulator[zoneName].push(cval);
    } else {
      accumulator[zoneName] = [cval];
    }
    return accumulator;
  }, {} as { [key: string]: Feature<Polygon>[] });

  // dissolve each group, if length decreases, it means that they are superfluous neigbors
  const zoneNames = Object.entries(groupedByZoneNames)
    .map(([zoneId, polygons]) => {
      const dissolved = dissolve(featureCollection(polygons));
      return dissolved.features.length < polygons.length ? zoneId : null;
    })
    .filter(Boolean);

  if (zoneNames.length > 0) {
    for (const x of zoneNames) {
      log(`${x} has neighbor with identical ID`);
    }
    throw new Error('Contains neighboring id zone');
  }
}

export function zeroOverlaps(
  fc: WorldFeatureCollection,
  { MIN_AREA_INTERSECTION }: GeoConfig
) {
  // add bbox to features to increase speed
  const features = getPolygons(fc).features.map((ft) => ({
    ft,
    bbox: bboxPolygon(bbox(ft)),
  }));

  const countriesToIgnore = new Set(
    fc.features
      .filter((ft) => ft.properties.isCombined)
      .map((ft) => ft.properties.countryKey)
  );

  const overlaps = features
    .filter(
      (ft1, index1) =>
        features.filter((ft2, index2) => {
          if (countriesToIgnore.has(ft1.ft.properties?.countryKey)) {
            return false;
          }
          if (index1 !== index2 && intersect(ft1.bbox, ft2.bbox)) {
            const intersection = intersect(ft1.ft, ft2.ft);
            if (intersection && area(intersection) > MIN_AREA_INTERSECTION) {
              return true;
            }
          }
        }).length
    )
    .map(({ ft, _ }: any) => ft.properties?.zoneName);
  if (overlaps.length > 0) {
    for (const x of overlaps) {
      console.error(`${x} overlaps with another feature`);
    }
    throw new Error('Feature(s) overlap');
  }
}

export { validateGeometry };
