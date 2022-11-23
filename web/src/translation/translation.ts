import { TFunction } from 'i18next';
import { useTranslation as useTranslationHook } from 'react-i18next';
import { vsprintf } from 'sprintf-js';
import i18next from './i18n';

// Todo: We should get rid of vsprintf and use i18next interpolation instead
const translateWithTranslator = (
  translator: TFunction,
  key: string,
  ...arguments_: string[]
) => {
  const translation = translator(key, '');
  if (arguments_.length > 0) {
    return vsprintf(translation, arguments_);
  }
  return translation;
};

// Used for translation outside of React components
export const translate = (key: string, ...arguments_: string[]) =>
  translateWithTranslator(i18next.t, key, ...arguments_);

// Hook for translations inside React components
export const useTranslation = () => {
  const { t, i18n } = useTranslationHook();
  const __ = (key: string, ...arguments_: string[]) =>
    translateWithTranslator(t, key, ...arguments_);
  return { __, i18n };
};

export const translateIfExists = (key: string) => {
  return i18next.exists(key) ? i18next.t(key) : '';
};

export const getZoneName = (zoneCode: string) =>
  translateIfExists(`zoneShortName.${zoneCode}.zoneName`);
export const getCountryName = (zoneCode: string) =>
  translateIfExists(`zoneShortName.${zoneCode}.countryName`);

/**
 * Gets the full name of a zone with the country name in parentheses.
 * @param {string} zoneCode
 * @returns string
 */
export function getZoneNameWithCountry(zoneCode: string) {
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

const DEFAULT_ZONE_NAME_LIMIT = 40;
/**
 * Gets the name of a zone with the country name in parentheses and zone-name ellipsified if too long.
 * @param {string} zoneCode
 * @returns string
 */
export function getShortenedZoneNameWithCountry(
  zoneCode: string,
  limit = DEFAULT_ZONE_NAME_LIMIT
) {
  const zoneName = getZoneName(zoneCode);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = getCountryName(zoneCode);
  if (!countryName) {
    return zoneName;
  }

  if (limit && zoneName.length > limit) {
    return `${zoneName.slice(0, Math.max(0, limit))}... (${countryName})`;
  }

  return `${zoneName} (${countryName})`;
}
