import { Feature, MultiPolygon, union } from '@turf/turf';
import { ZonesConfig, WorldFeatureCollection, FeatureProperties } from './types';

const emptyFeature: Feature<MultiPolygon, FeatureProperties> = {
  type: 'Feature',
  properties: {
    zoneName: '',
    countryKey: '',
    countryName: '',
    isHighestGranularity: false,
    isAggregatedView: true,
    isCombined: true,
  },
  geometry: { type: 'MultiPolygon', coordinates: [] },
};

const generateAggregates = (fc: WorldFeatureCollection, zones: ZonesConfig) => {
  const skippedZones: string[] = []; // Holds skipped subZones that are not in the geojson
  const { features } = fc;

  const countryZonesToCombine = Object.values(zones)
    .filter((zone) => zone.subZoneNames && zone.subZoneNames.length > 0)
    .map((zone) => zone.subZoneNames);

  const zonesToFlagAsNotAggregated = new Set(
    Object.values(zones)
      .filter((zone) => zone.subZoneNames && zone.subZoneNames.length > 0)
      .flatMap((zone) => zone.subZoneNames)
  );

  const unCombinedZones = features.map((feature) => {
    if (zonesToFlagAsNotAggregated.has(feature.properties.zoneName)) {
      feature.properties.isAggregatedView = false;
      feature.properties.isHighestGranularity = true;
      return feature;
    }
    feature.properties.isAggregatedView = true;
    feature.properties.isHighestGranularity = true;
    return feature;
  });

  const combinedZones = countryZonesToCombine
    .map((country) => {
      // TODO: Consider if should remove this check and just fail if country is undefined.
      // This was done to avoid having null-checks everywhere, but maybe it can be done it a
      // better way. See discussion here: https://github.com/electricitymaps/electricitymaps-contrib/pull/5179#discussion_r1131568845
      if (country === undefined) {
        return emptyFeature;
      }
      const multiZoneCountry = unCombinedZones.find(
        (feature) => feature.properties.zoneName === country[0]
      );
      const combinedCountry: Feature<MultiPolygon, FeatureProperties> = {
        ...emptyFeature,
        properties: {
          ...emptyFeature.properties,
          countryKey: multiZoneCountry?.properties.countryKey || '',
          zoneName: multiZoneCountry?.properties.countryKey || '',
          countryName: multiZoneCountry?.properties.countryName || '',
        },
      };

      for (const subZone of country) {
        const zoneToAdd = unCombinedZones.find(
          (feature) => feature.properties.zoneName === subZone
        );

        const combinedCountryPolygon = combinedCountry.geometry;
        if (zoneToAdd) {
          const unionGeometry = union(combinedCountryPolygon, zoneToAdd.geometry)
            ?.geometry as MultiPolygon;
          if (unionGeometry) {
            combinedCountry.geometry = unionGeometry;
          }
        } else {
          skippedZones.push(subZone);
        }
      }

      if (combinedCountry.properties && multiZoneCountry) {
        combinedCountry.properties['countryKey'] = multiZoneCountry.properties.countryKey;
        combinedCountry.properties['zoneName'] = multiZoneCountry.properties.countryKey;
      }

      return combinedCountry;
    })
    .filter((zone) => zone !== null);

  if (skippedZones.length > 0) {
    for (const zone of skippedZones) {
      console.error(
        `ERROR: Could not find geometry feature for ${zone}, make sure it has geometry in world.geojson.`
      );
    }
    process.exit(1);
  }
  return [...unCombinedZones, ...combinedZones];
};

export { generateAggregates };
