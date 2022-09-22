const { getJSON, writeJSON, fileExists } = require('./utilities');
const exchangeConfig = require('../../config/exchanges.json');

const generateExchangesToIgnore = (OUT_PATH, fc) => {
  console.log(`Generating new excluded-aggregated-exchanges.json...`); // eslint-disable-line no-console
  const fcCombined = {
    ...fc,
    features: fc.features.filter((feature) => {
      try {
        return feature.properties.isCombined;
      } catch (e) {
        console.log('Error: ', e, 'Feature: ', feature); // eslint-disable-line no-console
      }
    }),
  };

  const countryKeysToExclude = fcCombined.features.map((feature) => feature.properties.countryKey);

  const unCombinedExchanges = Object.keys(exchangeConfig).filter((key) => {
    const split = key.split('->');
    const zoneOne = split[0].slice(0, 2);
    const zoneTwo = split[1].slice(0, 2);
    if (zoneOne === zoneTwo && countryKeysToExclude.includes(key.slice(0, 2))) {
      return key;
    }
  });
  const exchanges = { exchangesToExclude: unCombinedExchanges };
  const existingExchanges = fileExists(OUT_PATH) ? getJSON(OUT_PATH) : {};
  if (JSON.stringify(exchanges) === JSON.stringify(existingExchanges)) {
    console.log(`No changes to excluded-aggregated-exchanges.json`); // eslint-disable-line no-console
    return;
  }

  writeJSON(OUT_PATH, exchanges);
};

module.exports = { generateExchangesToIgnore };
