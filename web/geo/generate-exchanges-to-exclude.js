const { mergeExchanges } = require('../generate-zones-config');
const { getJSON, writeJSON, fileExists } = require('./utilities');

const exchangeConfig = mergeExchanges();

const generateExchangesToIgnore = (OUT_PATH, zonesConfig) => {
  console.info(`Generating new excluded-aggregated-exchanges.json...`);
  const countryKeysToExclude = Object.keys(zonesConfig).filter((key) => {
    if (zonesConfig[key].subZoneNames?.length > 0) {
      return key;
    }
  });

  //Create a list of the exchange keys that we don't want to display in a country view
  const unCombinedExchanges = Object.keys(exchangeConfig).filter((key) => {
    const split = key.split('->');
    const zoneOne = split[0];
    const zoneTwo = split[1];

    const subzoneSplitOne = zoneOne.split('-');
    const subzoneSplitTwo = zoneTwo.split('-');
    if (
      (zoneOne.includes('-') && countryKeysToExclude.includes(subzoneSplitOne[0])) ||
      (zoneTwo.includes('-') && countryKeysToExclude.includes(subzoneSplitTwo[0]))
    ) {
      return key;
    }
  });

  //Create a list of the exchange keys that we don't want to display in the zone view
  const countryExchangesWithSubzones = Object.keys(exchangeConfig).filter((key) => {
    const split = key.split('->');
    const zoneOne = split[0];
    const zoneTwo = split[1];
    if (
      (!zoneOne.includes('-') && countryKeysToExclude.includes(zoneOne)) ||
      (!zoneTwo.includes('-') && countryKeysToExclude.includes(zoneTwo))
    ) {
      return key;
    }
  });
  const exchanges = {
    exchangesToExcludeCountryView: unCombinedExchanges,
    exchangesToExcludeZoneView: countryExchangesWithSubzones,
  };
  const existingExchanges = fileExists(OUT_PATH) ? getJSON(OUT_PATH) : {};
  if (JSON.stringify(exchanges) === JSON.stringify(existingExchanges)) {
    console.info(`No changes to excluded-aggregated-exchanges.json`);
    return;
  }

  writeJSON(OUT_PATH, exchanges);
};

module.exports = { generateExchangesToIgnore };
