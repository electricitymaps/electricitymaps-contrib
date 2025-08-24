import { useTranslation } from 'react-i18next';
import { useMatches } from 'react-router-dom';
import { baseUrl } from 'utils/constants';

/**
 * Generates the canonical url for the current page.
 */
export const useGetCanonicalUrl = () => {
  const { i18n } = useTranslation();

  const matches = useMatches();

  const pathname = matches?.at(-1)?.pathname ?? '/';

  const currentLanguageKey = i18n.languages[0];
  return `${baseUrl}${pathname}${
    currentLanguageKey.startsWith('en') ? '' : `?lang=${currentLanguageKey}`
  }`;
};
