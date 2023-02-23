import { Feature, MultiPolygon, Polygon, Properties, union } from '@turf/turf';
import type { ZoneConfig } from './types';

const generateAggregates = (geojson, zones: ZoneConfig) => {
  const skippedZones: string[] = []; // Holds skipped subZones that are not in the geojson
  const { features } = geojson;

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
      if (country === undefined) {
        return null;
      }
      const combinedCountry: Feature<MultiPolygon | Polygon, Properties> = {
        type: 'Feature',
        properties: {
          isHighestGranularity: false,
          isAggregatedView: true,
          isCombined: true,
        },
        geometry: { type: 'MultiPolygon', coordinates: [] },
      };
      const multiZoneCountry = unCombinedZones.find(
        (feature) => feature.properties.zoneName === country[0]
      );
      for (const subZone of country) {
        const zoneToAdd = unCombinedZones.find(
          (feature) => feature.properties.zoneName === subZone
        );

        const combinedCountryPolygon = combinedCountry.geometry as MultiPolygon;
        if (zoneToAdd) {
          const unionGeometry = union(
            combinedCountryPolygon,
            zoneToAdd.geometry
          )?.geometry;
          if (unionGeometry) {
            combinedCountry.geometry = unionGeometry;
          }
        } else {
          skippedZones.push(subZone);
        }
      }

      if (combinedCountry.properties) {
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
