/* eslint-disable prefer-rest-params */
/* eslint-disable prefer-spread */
// TODO: re-enable rules
// TODO: move to LinguiJS or react-intl that doesn't depend on the global
// object or a node.js process running.

import { vsprintf } from 'sprintf-js';

function translateWithLocale(locale, keyStr) {
  const keys = keyStr.split('.');
  let result = window.locales[locale];
  for (let i = 0; i < keys.length; i += 1) {
    if (result == null) { break; }
    result = result[keys[i]];
  }
  if (locale !== 'en' && !result) {
    return translateWithLocale('en', keyStr);
  }
  const formatArgs = Array.prototype.slice.call(arguments).slice(2); // remove 2 first
  return result && vsprintf(result, formatArgs);
}

export function translate() {
  const args = Array.prototype.slice.call(arguments);
  // Prepend locale
  args.unshift(window.locale);
  return translateWithLocale.apply(null, args);
}


export const getZoneName = (zoneCode) => translate(`zoneShortName.${zoneCode}.zoneName`);
export const getCountryName = (zoneCode) => translate(`zoneShortName.${zoneCode}.countryName`);

/**
 * Gets the full name of a zone with the country name in parentheses.
 * Zone name can be ellipsified with the limit parameter.
 * @param {string} zoneCode 
 * @param {number} limit 
 * @returns string
 */
 export function getZoneNameWithCountry(zoneCode, limit = 0) {
  const zoneName = getZoneName(zoneCode);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = getCountryName(zoneCode);
  if (!countryName) {
    return zoneName;
  }

  if (limit !== 0 && zoneName.length > limit) {
    return `${zoneName.substring(0, limit)}... (${countryName})`;
  }

  return `${zoneName} (${countryName})`;
}

export const __ = translate;
