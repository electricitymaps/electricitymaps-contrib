import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import yaml from 'js-yaml';

import { ZoneConfig } from './types';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));

const sortObjectByKey = (object: ZoneConfig) =>
  Object.keys(object)
    .sort()
    .reduce((result, key) => {
      result[key] = object[key];
      return result;
    }, {} as { [key: string]: ZoneConfig });

const saveZoneYaml = (zoneKey: string, zone: ZoneConfig) => {
  const zonePath = path.resolve(currentDirectory, `../../config/zones/${zoneKey}.yaml`);
  fs.writeFile(zonePath, yaml.dump(sortObjectByKey(zone)), (error) => {
    if (error) {
      console.error(error);
    }
  });
};

export { saveZoneYaml };
