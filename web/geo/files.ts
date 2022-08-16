// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'fs'.
const fs = require('fs');
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'path'.
const path = require('path');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getJSON'.
const { getJSON } = require('./utilities');

// @ts-expect-error TS(2304): Cannot find name '__dirname'.
const PATH_ZONES_JSON = path.resolve(__dirname, '../../config/zones.json');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getZonesJs... Remove this comment to see the full error message
const getZonesJson = () => getJSON(PATH_ZONES_JSON, 'utf8');

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'saveZonesJ... Remove this comment to see the full error message
const saveZonesJson = (zones: any) => {
  fs.writeFileSync(PATH_ZONES_JSON, JSON.stringify(zones, null, 2));
};

// @ts-expect-error TS(2580): Cannot find name 'module'. Do you need to install ... Remove this comment to see the full error message
module.exports = {
  getZonesJson,
  saveZonesJson,
};
