import { vsprintf } from 'sprintf-js';
import i18next from './i18n';
import { useTranslation as useTranslationHook } from 'react-i18next';

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
  const { t } = useTranslationHook();
  const __ = (key, ...args) => translateWithTranslator(t, key, ...args);
  return { __ };
};

export function translate() {
  const args = Array.prototype.slice.call(arguments);
  // Prepend locale
  args.unshift(window.locale);
  return translateWithLocale.apply(null, args);
}

export function getFullZoneName(zoneCode) {
  const zoneName = translate(`zoneShortName.${zoneCode}.zoneName`);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = translate(`zoneShortName.${zoneCode}.countryName`);
  if (!countryName) {
    return zoneName;
  }
  return `${zoneName} (${countryName})`;
}

export function getShortZoneName(zoneCode, limit = 40) {
  const zoneName = translate(`zoneShortName.${zoneCode}.zoneName`);
  if (!zoneName) {
    return zoneCode;
  }
  const countryName = translate(`zoneShortName.${zoneCode}.countryName`);
  if (!countryName) {
    return zoneName;
  }

  if (zoneName.length > limit) {
    return `${zoneName.substring(0, limit)}... (${countryName})`;
  }

  return `${zoneName} (${countryName})`;
}

export const __ = translate;
