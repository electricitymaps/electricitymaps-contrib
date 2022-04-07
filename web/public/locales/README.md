# Locales

## See translation status

Use the `translation-status.js` tool in `web` folder.

## Creating a new locale

We use a combination of [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) language codes and [ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#Officially_assigned_code_elements) country codes for our locale codes. The language code comes first, optionally followed by a country code if there are multiple locales for a language, separated by a hyphen (-). For example, Brazilian Portuguese is denoted by `pt-br`.

Create a file named YOUR_LOCALE.json in this directory with this content: "{}" (without the Double Quotation Marks). You will also need to update the files [web/locales-config.json](../../locales-config.json) and [mobileapp/www/index.html](../../../mobileapp/www/index.html).

Then start using the `translation-helper.js` tool in `web` folder.
