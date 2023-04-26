import yaml from 'js-yaml';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { ZoneConfig } from './types';

const sortObjectByKey = (object: ZoneConfig) =>
  Object.keys(object)
    .sort()
    .reduce((result, key) => {
      result[key] = object[key];
      return result;
    }, {} as { [key: string]: ZoneConfig });

const saveZoneYaml = (zoneKey: string, zone: ZoneConfig) => {
  const zonePath = path.resolve(
    fileURLToPath(new URL(`../../config/zones/${zoneKey}.yaml`, import.meta.url))
  );
  fs.writeFile(zonePath, yaml.dump(sortObjectByKey(zone)), (error) => {
    if (error) {
      console.error(error);
    }
  });
};

export { saveZoneYaml };
