import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { baseUrl } from 'utils/constants';

/**
 * Generates the canonical url for the current page.
 */
export const useGetCanonicalUrl = () => {
  const { i18n } = useTranslation();
  const { pathname } = useLocation();
  const currentLanguageKey = i18n.languages[0];
  return `${baseUrl}${pathname}${
    currentLanguageKey === 'en' ? '' : `?lang=${currentLanguageKey}`
  }`;
};
