const fs = require('fs');

const files = fs.readdirSync('/home/web/locales/')
  .filter(file => file.endsWith('.json'));

module.exports = files.map(file => file.replace('.json', ''));
