import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import yaml from 'js-yaml';

import { ZoneConfig } from './types';

const currentDirectory = path.dirname(fileURLToPath(import.meta.url));

const saveZoneYaml = (zoneKey: string, zone: ZoneConfig) => {
  const zonePath = path.resolve(currentDirectory, `../../config/zones/${zoneKey}.yaml`);
  fs.writeFile(zonePath, yaml.dump(zone, { sortKeys: true }), (error) => {
    if (error) {
      console.error(error);
    }
  });
};

export { saveZoneYaml };
