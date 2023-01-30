/* This script aggregates the per-zone config files into a single zones.json/exchanges.json
file to enable easy importing within web/ */
import * as yaml from 'js-yaml';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { round } from '../geo/utilities';

const BASE_CONFIG_PATH = '../../config';

const config = {
  verifyNoUpdates: process.env.VERIFY_NO_UPDATES !== undefined,
};

const mergeZones = () => {
  const basePath = path.resolve(__dirname, BASE_CONFIG_PATH, 'zones');

  const zoneFiles = fs.readdirSync(basePath);
  const filesWithDirectory = zoneFiles.map((file) => `${basePath}/${file}`);

  const UNNECESSARY_ZONE_FIELDS = new Set([
    'fallbackZoneMixes',
    'isLowCarbon',
    'isRenewable',
    'emissionFactors',
    'capacity',
    'comment',
    '_comment',
    'sources',
    'flag_file_name',
    'bypassedSubZones',
  ]);
  const zones = filesWithDirectory.reduce((zones, filepath) => {
    const zoneConfig: any = yaml.load(fs.readFileSync(filepath, 'utf8'));
    zoneConfig.bounding_box?.forEach((point: number[]) => {
      point[0] = round(point[0], 4);
      point[1] = round(point[1], 4);
    });

    for (const key in zoneConfig) {
      if (UNNECESSARY_ZONE_FIELDS.has(key)) {
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
  const basePath = path.resolve(__dirname, BASE_CONFIG_PATH, 'exchanges');

  const exchangeFiles = fs.readdirSync(basePath);
  const filesWithDirectory = exchangeFiles.map((file) => `${basePath}/${file}`);

  const UNNECESSARY_EXCHANGE_FIELDS = ['comment', '_comment', 'parsers'];

  const exchanges = filesWithDirectory.reduce((exchanges, filepath) => {
    const exchangeConfig: any = yaml.load(fs.readFileSync(filepath, 'utf8'));
    exchangeConfig.lonlat[0] = round(exchangeConfig.lonlat[0], 3);
    exchangeConfig.lonlat[1] = round(exchangeConfig.lonlat[1], 3);
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

  const defaultParameters: any = yaml.load(
    fs.readFileSync(`${basePath}/defaults.yaml`, 'utf8')
  );

  const zoneFiles = fs.readdirSync(`${basePath}/zones`);
  const filesWithDirectory = zoneFiles.map((file) => `${basePath}/zones/${file}`);

  const ratioParameters: any = {
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

  for (const filepath of filesWithDirectory) {
    const zoneConfig: any = yaml.load(fs.readFileSync(filepath, 'utf8'));
    const zoneKey = path.parse(filepath).name;
    for (const key in ratioParameters) {
      if (zoneConfig[key] !== undefined) {
        ratioParameters[key].zoneOverrides[zoneKey] = zoneConfig[key];
      }
    }
  }

  return ratioParameters;
};

const writeJSON = (fileName: any, object: any) => {
  const directory = path.resolve(path.dirname(fileName));

  if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory, { recursive: true });
  }

  fs.writeFileSync(fileName, JSON.stringify(object), { encoding: 'utf8' });
};

const zonesConfig = mergeZones();
const exchangesConfig = mergeExchanges();

const autogenConfigPath = path.resolve(__dirname, '../config');

if (config.verifyNoUpdates) {
  const zonesConfigPrevious = JSON.parse(
    fs.readFileSync(`${autogenConfigPath}/zones.json`, 'utf8')
  );
  const exchangesConfigPrevious = JSON.parse(
    fs.readFileSync(`${autogenConfigPath}/exchanges.json`, 'utf8')
  );
  if (JSON.stringify(zonesConfigPrevious) !== JSON.stringify(zonesConfig)) {
    console.error(
      'Did not expect any updates to zones.json. Please run "yarn generate-zones-config" to update.'
    );
    process.exit(1);
  }
  if (JSON.stringify(exchangesConfigPrevious) !== JSON.stringify(exchangesConfig)) {
    console.error(
      'Did not expect any updates to exchanges.json. Please run "yarn generate-zones-config" to update.'
    );
    process.exit(1);
  }
}

writeJSON(`${autogenConfigPath}/zones.json`, zonesConfig);
writeJSON(`${autogenConfigPath}/exchanges.json`, exchangesConfig);

export { mergeZones, mergeExchanges, mergeRatioParameters };
