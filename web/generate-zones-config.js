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

  const UNNECESSARY_ZONE_FIELDS = [
    'fallbackZoneMixes',
    'isLowCarbon',
    'isRenewable',
    'emissionFactors',
    'capacity',
    'comment',
    '_comment',
  ];
  const zones = filesWithDir.reduce((zones, filepath) => {
    const zoneConfig = yaml.load(fs.readFileSync(filepath, 'utf8'));
    for (const key in zoneConfig) {
      if (UNNECESSARY_ZONE_FIELDS.includes(key)) {
        delete zoneConfig[key];
      }
    }
    /*
     * The parsers object is only used to check if there is a production parser in the frontend.
     * This moves this check to the build step, so we can minimize the size of the frontend bundle.
     */
    if (zoneConfig?.parsers?.production?.length > 0) {
      zoneConfig.parsers = true;
    } else {
      zoneConfig.parsers = false;
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

  const UNNECESSARY_EXCHANGE_FIELDS = ['capacity', 'comment', '_comment', 'parsers'];

  const exchanges = filesWithDir.reduce((exchanges, filepath) => {
    const exchangeConfig = yaml.load(fs.readFileSync(filepath, 'utf8'));
    for (const key in exchangeConfig) {
      if (UNNECESSARY_EXCHANGE_FIELDS.includes(key)) {
        delete exchangeConfig[key];
      }
    }
    const exchangeKey = path.parse(filepath).name.split('_').join('->');
    Object.assign(exchanges, { [exchangeKey]: exchangeConfig });
    return exchanges;
  }, {});

  return exchanges;
};

const mergeRatioParameters = () => {
  // merge the fallbackZoneMixes, isLowCarbon, isRenewable params into a single object
  const basePath = path.resolve(__dirname, '../config');

  const defaultParameters = yaml.load(fs.readFileSync(`${basePath}/defaults.yaml`, 'utf8'));

  const zoneFiles = fs.readdirSync(`${basePath}/zones`);
  const filesWithDir = zoneFiles.map((file) => `${basePath}/zones/${file}`);

  const ratioParameters = {
    fallbackZoneMixes: {
      defaults: defaultParameters.fallbackZoneMixes,
      zoneOverrides: {},
    },
    isLowCarbon: {
      defaults: defaultParameters.isLowCarbon,
      zoneOverrides: {},
    },
    isRenewable: {
      defaults: defaultParameters.isRenewable,
      zoneOverrides: {},
    },
  };

  filesWithDir.forEach((filepath) => {
    const zoneConfig = yaml.load(fs.readFileSync(filepath, 'utf8'));
    const zoneKey = path.parse(filepath).name;
    for (const key in ratioParameters) {
      if (zoneConfig[key] !== undefined) {
        ratioParameters[key].zoneOverrides[zoneKey] = zoneConfig[key];
      }
    }
  });

  return ratioParameters;
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

const autogenConfigPath = path.resolve(__dirname, 'src/config');

if (config.verifyNoUpdates) {
  const zonesConfigPrevious = JSON.parse(fs.readFileSync(`${autogenConfigPath}/zones.json`, 'utf8'));
  const exchangesConfigPrevious = JSON.parse(fs.readFileSync(`${autogenConfigPath}/exchanges.json`, 'utf8'));
  if (JSON.stringify(zonesConfigPrevious) !== JSON.stringify(zonesConfig)) {
    console.error('Did not expect any updates to zones.json. Please run "yarn generate-zones-config" to update.');
    process.exit(1);
  }
  if (JSON.stringify(exchangesConfigPrevious) !== JSON.stringify(exchangesConfig)) {
    console.error('Did not expect any updates to exchanges.json. Please run "yarn generate-zones-config" to update.');
    process.exit(1);
  }
}

writeJSON(`${autogenConfigPath}/zones.json`, zonesConfig);
writeJSON(`${autogenConfigPath}/exchanges.json`, exchangesConfig);

// export merge function
module.exports = {
  mergeZones,
  mergeExchanges,
  mergeRatioParameters,
};
