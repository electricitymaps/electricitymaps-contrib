const fs = require('fs');
const readline = require('readline-sync');
require('colors');

const LOCALES_PATH = './public/locales/';

const languages = fs.readdirSync(LOCALES_PATH)
  .filter(f => f !== 'en.json' && f.endsWith('.json'))
  .map(f => f.replace('.json', ''));

console.log(`Languages you can translate: ${languages.join(', ').green}`);
const language = readline.question('Which language do you want to translate: ');
if (!languages.includes(language)) {
  console.error((`${language} is not a translatable language!`).red);
  process.exit(1);
}

console.log();

const en = JSON.parse(fs.readFileSync(`${LOCALES_PATH}/en.json`));
const other = JSON.parse(fs.readFileSync(`${LOCALES_PATH}/${language}.json`));

function checkUntranslated(e, o, p) {
  if (typeof e === 'string') {
    if (o === undefined) {
      // eslint-disable-next-line no-param-reassign
      o = readline.question(`${p.slice(0, -1).blue} [${e.green}]: `);
    }
  } else {
    Object.keys(e).forEach(key => {
      const t = checkUntranslated(e[key], o !== undefined ? o[key]: undefined, `${p + key}.`);
      if (t !== '') {
        if (o === undefined) {
          // eslint-disable-next-line no-param-reassign
          o = {};
        }
        o[key] = t;
      }
    });
  }
  return o;
}

fs.writeFileSync(`${LOCALES_PATH}/${language}.json`, JSON.stringify(checkUntranslated(en, other, ''), null, 4));
console.log('Finished!');
