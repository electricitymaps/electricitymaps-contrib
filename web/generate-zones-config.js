/* This script aggregates the per-zone config files into a single zones.json/exchanges.json
file to enable easy importing within web/ */
const yaml = require('js-yaml');
const path = require('path');
const fs = require('fs');

const config = {
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const mergeZones = () => {
  const basePath = path.resolve(__dirname, '../config/zones');

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
  const basePath = path.resolve(__dirname, '../config/exchanges');

  const exchangeFiles = fs.readdirSync(basePath);
  const filesWithDir = exchangeFiles.map((file) => `${basePath}/${file}`);

  const exchanges = filesWithDir.reduce((exchanges, filepath) => {
    const exchangeKey = path.parse(filepath).name.split('→').join('->');
    Object.assign(exchanges, { [exchangeKey]: yaml.load(fs.readFileSync(filepath, 'utf8')) });
    return exchanges;
  }, {});

  return exchanges;
};

const writeJSON = (fileName, obj, encoding = 'utf8') => {
  const dir = path.resolve(path.dirname(fileName));

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  fs.writeFileSync(fileName, JSON.stringify(obj), encoding);
};

const zonesConfig = mergeZones();
const exchangesConfig = mergeExchanges();

if (config.verifyNoUpdates) {
  const zonesConfigPrevious = JSON.parse(fs.readFileSync('src/config/zones.json', 'utf8'));
  const exchangesConfigPrevious = JSON.parse(fs.readFileSync('src/config/exchanges.json', 'utf8'));
  if (JSON.stringify(zonesConfigPrevious) !== JSON.stringify(zonesConfig)) {
    console.error('Did not expect any updates to zones.json. Please run "yarn generate-zones-config" to update.');
    process.exit(1);
  }
  if (JSON.stringify(exchangesConfigPrevious) !== JSON.stringify(exchangesConfig)) {
    console.error('Did not expect any updates to exchanges.json. Please run "yarn generate-zones-config" to update.');
    process.exit(1);
  }
}

writeJSON('src/config/zones.json', zonesConfig);
writeJSON('src/config/exchanges.json', exchangesConfig);

// export merge function
module.exports = {
  mergeZones,
  mergeExchanges,
};
