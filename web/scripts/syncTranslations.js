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
    if (!reference[key] || typeof reference[key] !== typeof language[key]) {
      // Delete the key from the current language if not present in the reference
      // or if the type of the key is different
      delete language[key];
    } else if (typeof language[key] === 'object' && typeof reference[key] === 'object') {
      // Recursively clean nested objects
      cleanLanguageObject(language[key], reference[key]);
    }
  }
  // Run through the keys again to remove any empty objects
  for (const key of Object.keys(language)) {
    if (typeof language[key] === 'object' && Object.keys(language[key]).length === 0) {
      delete language[key];
    }
  }
}

for (const language of languages) {
  // Read the language file
  console.log(`🧹 Fixing ${language.replace('.json', '')}...`);
  let languageFile = await readFile(LOCALES_PATH + language);
  // Parse the language file
  languageFile = JSON.parse(languageFile);
  // Clean the language object
  cleanLanguageObject(languageFile, englishFile);
  await writeFile(LOCALES_PATH + language, JSON.stringify(languageFile, null, 2));
  console.log(`✅ Fixed ${language.replace('.json', '')}`);
}
