const fs = require('fs');

const files = fs.readdirSync('./locales')
  .filter(file => file.endsWith('.json'));

const locales = files.map(file => file.replace('.json', ''));

const localesString = JSON.stringify(locales)
  .replace(/"/g, '\'')
  .replace(/,/g, ', ');

fs.writeFileSync('./locales/locales-list.js', `module.exports = ${localesString};\n`);

const test = require('./locales/locales-list');

if (JSON.stringify(locales) !== JSON.stringify(test)) {
  console.error('Locale list generation failed', locales, test);
  process.exit(1);
}
