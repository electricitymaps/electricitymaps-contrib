const { union } = require('@turf/turf');

const generateAggregates = (geojson) => {
  const { features } = geojson;
  const unCombinedCountries = ['AU', 'BR', 'CA', 'CL', 'JP', 'MY', 'US', 'MX'];

  const countryKeys = [...new Set(features.map((feature) => feature.properties.countryKey))];

  const combinedZoneKeys = countryKeys.filter((x) => !unCombinedCountries.includes(x));

  const zonesNotToAggregate = unCombinedCountries
    .map((countryKey) => {
      const unCombinedZones = features.filter((feature) => feature.properties.countryKey === countryKey);

      return unCombinedZones;
    })
    .flatMap((feautures) => {
      for (let i = 0; i < feautures.length; i++) {
        feautures[i].properties.aggregatedView = true;
      }
      return feautures;
    });

  const zonesToAggregate = combinedZoneKeys
    .map((countryKey) => {
      const combinedZones = features.filter((feature) => feature.properties.countryKey === countryKey);

      return combinedZones;
    })
    .map((zonesToCombine) => {
      if (zonesToCombine.length === 1) {
        zonesToCombine[0].properties.aggregatedView = true;
        return zonesToCombine[0];
      }
      if (zonesToCombine.length > 1) {
        const multiZoneCountry = zonesToCombine[0];

        for (let i = 1; i < zonesToCombine.length; i++) {
          multiZoneCountry.geometry = union(multiZoneCountry.geometry, zonesToCombine[i].geometry).geometry;
        }
        multiZoneCountry.properties.aggregatedView = true;
        multiZoneCountry.properties.isCombined = true;
        multiZoneCountry.properties.zoneName = multiZoneCountry.properties.countryKey;
        return multiZoneCountry;
      }
    });

  return zonesToAggregate.concat(zonesNotToAggregate);
};

module.exports = { generateAggregates };
