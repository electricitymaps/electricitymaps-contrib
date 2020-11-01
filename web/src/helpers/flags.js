/* eslint-disable */
// TODO: remove once refactored

var exports = module.exports = {};

var zones = require('../../../config/zones.json');

var { DEFAULT_FLAG_SIZE } = require('../helpers/constants');

exports.flagUri = function(countryCode, flagSize = DEFAULT_FLAG_SIZE) {
  if (!countryCode) return undefined;
  var zoneFlagFile = (zones[countryCode.toUpperCase()] || {}).flag_file_name;
  var flagFile = zoneFlagFile || (countryCode.toLowerCase().split('-')[0] + '.png');
  return resolvePath('images/flag-icons/flags_iso/' + flagSize + '/' + flagFile);
}
