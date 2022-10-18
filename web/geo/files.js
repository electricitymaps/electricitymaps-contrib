const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

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
  saveZoneYaml,
};
