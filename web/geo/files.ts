const fs = require('fs');
const path = require('path');

const { getJSON } = require('./utilities');

const PATH_ZONES_JSON = path.resolve(__dirname, '../../config/zones.json');

const getZonesJson = () => getJSON(PATH_ZONES_JSON, 'utf8');

const saveZonesJson = (zones) => {
  fs.writeFileSync(PATH_ZONES_JSON, JSON.stringify(zones, null, 2));
};

module.exports = {
  getZonesJson,
  saveZonesJson,
};
