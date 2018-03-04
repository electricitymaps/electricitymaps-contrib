var exports = module.exports = {};

var zones = require('../../../config/zones.json');

exports.flagUri = function(countryCode, flagSize) {
  var zoneFlagFile = (zones[countryCode.toUpperCase()] || {}).flag_file_name;
  var flagFile = zoneFlagFile || (countryCode.toLowerCase().split('-')[0] + '.png');
  return 'images/flag-icons/flags_iso/' + flagSize + '/' + flagFile;
}
