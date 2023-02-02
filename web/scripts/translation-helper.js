const fs = require('fs');
const readline = require('readline-sync');
const path = require('path');
const process = require('process');
require('colors');

const LOCALES_PATH = path.join(__dirname, '..', 'public/locales/');

function saveTemporaryStateToFile(key, language, file) {
  fs.writeFileSync(`${LOCALES_PATH}/${language}.json`, JSON.stringify(file, null, 2));
  console.info(`Saved ${key}...`.yellow.italic);
}

const languages = fs
  .readdirSync(LOCALES_PATH)
  .filter((f) => f !== 'en.json' && f.endsWith('.json'))
  .map((f) => f.replace('.json', ''));

console.info('\nTranslation helper\n'.underline.bold.cyan);
console.info(
  ' WARNING:'.bgYellow.black,
  'Input is only saved after completing a full group of translations!\n'.yellow
);
console.info(`Languages you can translate: ${languages.join(', ').green}`);

const language = readline.question('Which language do you want to translate: ');
if (!languages.includes(language)) {
  console.error(`${language} is not a translatable language!`.red);
  process.exit(1);
}

const en = JSON.parse(fs.readFileSync(`${LOCALES_PATH}/en.json`));
const other = JSON.parse(fs.readFileSync(`${LOCALES_PATH}/${language}.json`));

function checkUntranslated(e, o, p) {
  if (typeof e === 'string') {
    if (o === undefined) {
      // eslint-disable-next-line no-param-reassign
      o = readline.question(`${p.slice(0, -1).blue} [${e.green}]: `);
    }
  } else {
    Object.keys(e).forEach((key) => {
      const t = checkUntranslated(
        e[key],
        o !== undefined ? o[key] : undefined,
        `${p + key}.`
      );
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

// Find top level keys in other
Object.keys(en).forEach((key) => {
  let isNew = other[key] ? false : true;
  const t = checkUntranslated(en[key], other[key], `${key}.`);
  if (t !== '') {
    other[key] = t;
    if (isNew) {
      saveTemporaryStateToFile(key, language, other);
    }
  }
});

console.info('\nYou have translated everything!\n'.rainbow);
