import { readdir, readFile, writeFile } from 'node:fs/promises';

const LOCALES_PATH = './src/locales/';

// First, await the result of readdir
const files = await readdir(LOCALES_PATH);
// Then, filter the files to get all languages
const all_languages = files.filter((file) => file.endsWith('.json'));

// Extract the english file to use as a master reference from the list of all languages
const english = all_languages.find((f) => f === 'en.json');

// Remove the english file from the list of all languages
const languages = all_languages.filter((f) => f !== 'en.json');
const englishFile = JSON.parse(await readFile(LOCALES_PATH + english));

function cleanLanguageObject(language, reference) {
  for (const key of Object.keys(language)) {
    console.log(key);
    if (!reference[key]) {
      console.log(key);
      // Delete the key from the current language if not present in the reference
      delete language[key];
    } else if (typeof language[key] === 'object' && typeof reference[key] === 'object') {
      // Recursively clean nested objects
      cleanLanguageObject(language[key], reference[key]);
    }
  }
}

for (const language of languages) {
  // Read the language file
  let languageFile = await readFile(LOCALES_PATH + language);
  // Parse the language file
  languageFile = JSON.parse(languageFile);
  console.log(languageFile);
  // Clean the language object
  cleanLanguageObject(languageFile, englishFile);
  await writeFile(LOCALES_PATH + language, JSON.stringify(languageFile, null, 2));
}
