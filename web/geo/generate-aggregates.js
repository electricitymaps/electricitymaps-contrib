const { union } = require('@turf/turf');

const generateAggregates = (geojson) => {
  const { features } = geojson;

  const countryKeys = [...new Set(features.map((feature) => feature.properties.countryKey))];

  const aggregates = countryKeys
    .map((countryKey) => {
      const combinedZones = features.filter((feature) => feature.properties.countryKey === countryKey);

      return combinedZones;
    })
    .map((countries) => {
      if (countries.length === 1) {
        countries[0].properties.aggregated = true;
        countries[0].properties.higestFidelityView = true; //todo add false value for detailed zones
        return countries[0];
      }
      if (countries.length > 1) {
        const multiZoneCountry = countries[0];

        for (let i = 1; i < countries.length; i++) {
          multiZoneCountry.geometry = union(multiZoneCountry.geometry, countries[i].geometry).geometry;
        }
        countries[0].properties.aggregated = true;
        countries[0].properties.higestFidelityView = true; //todo
        countries[0].properties.zoneName = countries[0].properties.countryKey;
        return multiZoneCountry;
      }
    });

  return aggregates;
};

module.exports = { generateAggregates };
