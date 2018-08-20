const {translate} = require('deepl-translator');
const deepmerge = require('deepmerge');
const fs = require('fs');

const translatable = ['de', 'fr', 'es', 'it', 'nl', 'pl'];
let files = process.argv.slice(2);
if (files.length === 0) {
  files = translatable.map(s => {
    return s + '.json';
  });
}
files = files.filter(file => {
  return file !== 'en.json' && translatable.includes(file.slice(0, -5)) && !file.startsWith('gen');
});
if (files.length === 0) {
  console.log('No translatable file found!');
  return;
}

function processFile(file) {
  return new Promise(resolve => {
    const en = JSON.parse(fs.readFileSync(__dirname + '/locales/en.json'));
    const out = deepmerge(en, JSON.parse(fs.readFileSync(__dirname + '/locales/' + file)));

    let pending = 0;
    let finished = 0;

    for (const key1 in out) {
      if (typeof out[key1] === 'string') {
        if (en[key1] !== undefined) {
          if (en[key1] === out[key1]) {
            pending++;
            translate(out[key1], file.slice(0, -5).toUpperCase()).then(res => {
              out[key1] = res.translation;
              finished++;
              checkFinish();
            }).catch(() => {
            });
          }
        }
      } else {
        for (const key2 in out[key1]) {
          if (typeof out[key1][key2] === 'string') {
            if (en[key1] !== undefined) {
              if (en[key1][key2] === out[key1][key2]) {
                pending++;
                translate(out[key1][key2], file.slice(0, -5).toUpperCase()).then(res => {
                  out[key1][key2] = res.translation;
                  finished++;
                  checkFinish();
                }).catch(() => {
                });
              }
            }
          } else {
            for (const key3 in out[key1][key2]) {
              if (typeof out[key1][key2][key3] === 'string') {
                if (en[key1][key2] !== undefined) {
                  if (en[key1][key2][key3] === out[key1][key2][key3]) {
                    pending++;
                    translate(out[key1][key2][key3], file.slice(0, -5).toUpperCase()).then(res => {
                      out[key1][key2][key3] = res.translation;
                      finished++;
                      checkFinish();
                    })
                  }
                }
              } else {
                console.log(out[key1][key2][key3]);
              }
            }
          }
        }
      }
    }

    function checkFinish() {
      if (finished === pending) {
        console.log('Finished ' + file.slice(0, -5));
        fs.writeFileSync(__dirname + '/locales/' + file, JSON.stringify(out, null, 4));
        resolve();
      }
    }
  });
}

function next() {
  const file = files.shift();
  processFile(file).then(() => {
    if (files.length === 0) {
    } else {
      next();
    }
  });
}

next();
