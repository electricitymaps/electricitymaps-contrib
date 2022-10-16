const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const { getJSON } = require('./utilities');

const PATH_ZONES_JSON = path.resolve(__dirname, '../../config/zones.json');

const getZonesJson = () => getJSON(PATH_ZONES_JSON, 'utf8');

const saveZonesJson = (zones) => {
  fs.writeFileSync(PATH_ZONES_JSON, JSON.stringify(zones, null, 2));
};

const saveZoneYaml = (zoneKey, zone) => {
  const zonePath = path.resolve(__dirname, `../../config/zones/${zoneKey}.yaml`);
  const sortObjectByKey = (obj) =>
    Object.keys(obj)
      .sort()
      .reduce((result, key) => {
        result[key] = obj[key];
        return result;
      }, {});
  fs.writeFile(zonePath, yaml.dump(sortObjectByKey(zone)), (err) => {
    if (err) {
      console.error(err);
    }
  });
};

module.exports = {
  getZonesJson,
  saveZonesJson,
  saveZoneYaml,
};
