import { readdir, readFile } from 'node:fs/promises';

const LOCALES_PATH = './web/src/locales/';

// First, await the result of readdir
const files = await readdir(LOCALES_PATH);
// Then, filter the files to get all languages
const all_languages = files.filter((file) => file.endsWith('.json'));

// Extract the english file to use as a master reference from the list of all languages
const english = all_languages.find((f) => f === 'en.json');

// Remove the english file from the list of all languages
const languages = all_languages.filter((f) => f !== 'en.json');
const englishFile = JSON.parse(await readFile(LOCALES_PATH + english));

function detectTranslationsOutOfSync(language, reference) {
  for (const key of Object.keys(language)) {
    if (!reference[key] || typeof reference[key] !== typeof language[key]) {
      console.log(
        'One or more translation files are out of sync. Run the script syncTranslations to fix it.'
      );
      process.exit(1);
    } else if (typeof language[key] === 'object' && typeof reference[key] === 'object') {
      // Recursively clean nested objects
      detectTranslationsOutOfSync(language[key], reference[key]);
    }
  }
}

for (const language of languages) {
  // Read the language file
  let languageFile = await readFile(LOCALES_PATH + language);
  // Parse the language file
  languageFile = JSON.parse(languageFile);
  // Clean the language object
  detectTranslationsOutOfSync(languageFile, englishFile);
}
