# Locales

## See translation status

Use the `translation-status.js` tool in `web/scripts` folder.

## Creating a new locale

We use a combination of [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) language codes and [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements) country codes for our locale codes. The language code comes first, optionally followed by an uppercase country code if there are multiple locales for a language, separated by a hyphen (-). For example, Brazilian Portuguese is denoted by `pt-BR`.

See more info and examples here: https://www.w3.org/International/articles/language-tags/#region

Create a file named YOUR_LOCALE.json in this directory with this content: "{}" (without the Double Quotation Marks). You will also need to update the files [../../src/translation/locales.ts](../../src/translation/locales.ts).

Then start using the `translation-helper.js` tool in `web/scripts` folder.
