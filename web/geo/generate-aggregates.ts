import { Feature, MultiPolygon, Polygon, Properties, union } from '@turf/turf';
import { ZoneConfig } from './types';

const generateAggregates = (geojson, zones: ZoneConfig) => {
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
      for (const element of country) {
        const zoneToAdd = unCombinedZones.find(
          (feature) => feature.properties.zoneName === element
        );

        const combinedCountryPolygon = combinedCountry.geometry as MultiPolygon;

        const unionGeometry = union(combinedCountryPolygon, zoneToAdd.geometry)?.geometry;

        if (unionGeometry) {
          combinedCountry.geometry = unionGeometry;
        }
      }

      if (combinedCountry.properties) {
        combinedCountry.properties['countryKey'] = multiZoneCountry.properties.countryKey;
        combinedCountry.properties['zoneName'] = multiZoneCountry.properties.countryKey;
      }

      return combinedCountry;
    })
    .filter((zone) => zone !== null);

  return unCombinedZones.concat(combinedZones);
};

export { generateAggregates };
