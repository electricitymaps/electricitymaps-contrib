import { vsprintf } from 'sprintf-js';
import { useTranslation as useTranslationHook } from 'react-i18next';
import i18next from './i18n';

// Todo: We should get rid of vsprintf and use i18next interpolation instead
const translateWithTranslator = (translator, key, ...args) => {
  const translation = translator(key, '');
  if (args.length > 0) {
    return vsprintf(translation, args);
  }
  return translation;
};

// Used for translation outside of React components
export const translate = (key, ...args) => translateWithTranslator(i18next.t, key, ...args);

// Hook for translations inside React components
export const useTranslation = () => {
  const { t, i18n } = useTranslationHook();
  const __ = (key, ...args) => translateWithTranslator(t, key, ...args);
  return { __, i18n };
};

export const translateIfExists = (key) => {
  return i18next.exists(key) ? i18next.t(key) : '';
};

export const getZoneName = (zoneCode) => translateIfExists(`zoneShortName.${zoneCode}.zoneName`);
export const getCountryName = (zoneCode) => translateIfExists(`zoneShortName.${zoneCode}.countryName`);

/**
 * Gets the full name of a zone with the country name in parentheses.
 * @param {string} zoneCode
 * @returns string
 */
export function getZoneNameWithCountry(zoneCode) {
  const zoneName = getZoneName(zoneCode);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = getCountryName(zoneCode);
  if (!countryName) {
    return zoneName;
  }

  return `${zoneName} (${countryName})`;
}

/**
 * Gets the name of a zone with the country name in parentheses and zone-name ellipsified if too long.
 * @param {string} zoneCode
 * @returns string
 */
export function getShortenedZoneNameWithCountry(zoneCode, limit = 40) {
  const zoneName = getZoneName(zoneCode);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = getCountryName(zoneCode);
  if (!countryName) {
    return zoneName;
  }

  if (limit && zoneName.length > limit) {
    return `${zoneName.substring(0, limit)}... (${countryName})`;
  }

  return `${zoneName} (${countryName})`;
}
