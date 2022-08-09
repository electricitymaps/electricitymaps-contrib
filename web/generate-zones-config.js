const yaml = require('js-yaml');
const path = require('path');
const fs = require('fs');

const mergeZones = () => {
  const basePath = '../config/zones';

  const zoneFiles = fs.readdirSync(basePath);
  const filesWithDir = zoneFiles.map((file) => `${basePath}/${file}`);

  const UNNECESSARY_ZONE_FIELDS = ['fallbackZoneMixes', 'isLowCarbon', 'isRenewable', 'emissionFactors'];
  const zones = filesWithDir.reduce((zones, filepath) => {
    const zoneConfig = yaml.load(fs.readFileSync(filepath, 'utf8'));
    for (const key in zoneConfig) {
      if (UNNECESSARY_ZONE_FIELDS.includes(key)) {
        delete zoneConfig[key];
      }
    }
    Object.assign(zones, { [path.parse(filepath).name]: zoneConfig });
    return zones;
  }, {});

  return zones;
};

const mergeExchanges = () => {
  const basePath = '../config/exchanges';

  const exchangeFiles = fs.readdirSync(basePath);
  const filesWithDir = exchangeFiles.map((file) => `${basePath}/${file}`);

  const exchanges = filesWithDir.reduce(
    (exchanges, filepath) =>
      Object.assign(exchanges, { [path.parse(filepath).name]: yaml.load(fs.readFileSync(filepath, 'utf8')) }),
    {}
  );

  return exchanges;
};

const zonesConfig = mergeZones();
const exchangesConfig = mergeExchanges();

module.exports = {
  zonesConfig,
  exchangesConfig,
};
