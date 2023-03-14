import yaml from 'js-yaml';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const sortObjectByKey = (object: any) =>
  Object.keys(object)
    .sort()
    .reduce((result, key) => {
      result[key] = object[key];
      return result;
    }, {});

const saveZoneYaml = (zoneKey: string, zone: any) => {
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
