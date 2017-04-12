var exports = module.exports = {};

var zones = require('json-loader!./configs/zones.json');

exports.flagUri = function(countryCode, flagSize) {
  var flagFile = (zones[countryCode.toUpperCase()] || {}).flag_file_name || (countryCode.toLowerCase() + '.png');
  return 'images/flag-icons/flags_iso/' + flagSize + '/' + flagFile;
}
