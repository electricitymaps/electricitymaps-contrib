import { mergeExchanges } from '../scripts/generateZonesConfig.js';
import { ZonesConfig } from './types.js';
import { fileExists, getJSON, writeJSON } from './utilities.js';

const exchangeConfig = mergeExchanges();

const generateExchangesToIgnore = (OUT_PATH: string, zonesConfig: ZonesConfig) => {
  console.info(`Generating new excludedAggregatedExchanges.json...`);
  const countryKeysToExclude = new Set(
    Object.keys(zonesConfig).filter((key) => {
      if ((zonesConfig[key].subZoneNames ?? []).length > 0) {
        return key;
      }
    })
  );

  //Create a list of the exchange keys that we don't want to display in a country view
  const unCombinedExchanges = Object.keys(exchangeConfig).filter((key) => {
    const split = key.split('->');
    const zoneOne = split[0];
    const zoneTwo = split[1];

    const subzoneSplitOne = zoneOne.split('-');
    const subzoneSplitTwo = zoneTwo.split('-');
    if (
      (zoneOne.includes('-') && countryKeysToExclude.has(subzoneSplitOne[0])) ||
      (zoneTwo.includes('-') && countryKeysToExclude.has(subzoneSplitTwo[0]))
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
      (!zoneOne.includes('-') && countryKeysToExclude.has(zoneOne)) ||
      (!zoneTwo.includes('-') && countryKeysToExclude.has(zoneTwo))
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
    console.info(`No changes to excludedAggregatedExchanges.json`);
    return;
  }

  writeJSON(OUT_PATH, exchanges);
};

export { generateExchangesToIgnore };
