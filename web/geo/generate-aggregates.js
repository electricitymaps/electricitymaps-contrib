const { union } = require('@turf/turf');

const generateAggregates = (geojson, zones) => {
  const { features } = geojson;

  const subzonesToCombine = Object.values(zones)
    .filter((zone) => !zone?.hasGeometry && zone?.subZoneNames?.length > 0)
    .map((zone) => zone.subZoneNames);

  const zonesToFlagAsNotAggregated = Object.values(zones)
    .filter((zone) => zone?.subZoneNames?.length > 0)
    .flatMap((zone) => zone.subZoneNames);

  const unCombinedZones = features.map((feature) => {
    if (zonesToFlagAsNotAggregated.includes(feature.properties.zoneName)) {
      feature.properties.isAggregatedView = false;
      feature.properties.isHighestGranularity = true;
      return feature;
    }
    feature.properties.isAggregatedView = true;
    feature.properties.isHighestGranularity = true;
    return feature;
  });

  const combinedZones = subzonesToCombine.map((subzone) => {
    const combinedCountry = {
      type: 'Feature',
      properties: {
        isHighestGranularity: false,
        isAggregatedView: true,
        isCombined: true,
      },
      geometry: { type: 'MultiPolygon', coordinates: [] },
    };
    const [multiZoneCountry] = unCombinedZones.filter((feature) => feature.properties.zoneName === subzone[0]);
    for (let i = 0; i < subzone.length; i++) {
      const [zoneToAdd] = unCombinedZones.filter((feature) => feature.properties.zoneName === subzone[i]);
      combinedCountry.geometry = union(combinedCountry.geometry, zoneToAdd.geometry).geometry;
    }
    combinedCountry.properties.countryKey = multiZoneCountry.properties.countryKey;
    combinedCountry.properties.zoneName = multiZoneCountry.properties.countryKey;
    return combinedCountry;
  });

  return unCombinedZones.concat(combinedZones);
};

module.exports = { generateAggregates };
