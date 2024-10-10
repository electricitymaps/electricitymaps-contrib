import { useTranslation } from 'react-i18next';
import { useMatch } from 'react-router-dom';
import { baseUrl } from 'utils/constants';

/**
 * Generates the canonical url for the current page.
 */
export const useGetCanonicalUrl = () => {
  const { i18n } = useTranslation();
  // TODO: Replace with useMatches once we have migrated to react routers data routing
  const mapMatch = useMatch('/map');
  const zoneMatch = useMatch('/zone/:zoneId');

  const pathname = mapMatch?.pathname ?? zoneMatch?.pathname;

  const currentLanguageKey = i18n.languages[0];
  return `${baseUrl}${pathname ?? '/map'}${
    currentLanguageKey.startsWith('en') ? '' : `?lang=${currentLanguageKey}`
  }`;
};
