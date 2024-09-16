import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { baseUrl } from 'utils/constants';

/**
 * Generates the canonical link for the current page.
 * The returned element should be placed inside a Helmet component to function correctly.
 */
export const useGetCanonicalLink = () => {
  const { i18n } = useTranslation();
  const { pathname } = useLocation();
  const currentLanguageKey = i18n.languages[0];
  return (
    <link
      rel="canonical"
      href={`${baseUrl}${pathname}${
        currentLanguageKey == 'en' ? '' : `?lang=${currentLanguageKey}`
      }`}
    />
  );
};
