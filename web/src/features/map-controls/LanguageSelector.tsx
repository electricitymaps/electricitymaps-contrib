import { Button } from 'components/Button';
import { Languages } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { languageNames } from 'translation/locales';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

import MapButton from './MapButton';
import MapOptionSelector from './MapOptionSelector';

type LanguageNamesKey = keyof typeof languageNames;

export function LanguageSelector({ isMobile }: { isMobile?: boolean }) {
  const { t, i18n } = useTranslation();
  const languageKeys = Object.keys(languageNames) as Array<LanguageNamesKey>;
  const currentLanguageKey = i18n.language as LanguageNamesKey;
  const [selectedLanguage, setSelectedLanguage] = useState(
    languageNames[currentLanguageKey] ?? 'English'
  );

  const handleLanguageSelect = (languageKey: LanguageNamesKey) => {
    i18n.changeLanguage(languageKey);
    setSelectedLanguage(languageNames[languageKey]);
    trackEvent(TrackEvent.LANGUAGE_SELECTED, { language: languageNames[languageKey] });
  };
  return (
    <MapOptionSelector
      trigger={
        isMobile ? (
          <Button
            size="lg"
            type="secondary"
            icon={<Languages size={20} />}
            backgroundClasses="w-[330px] h-[45px]"
          >
            {t('tooltips.selectLanguage')}
          </Button>
        ) : (
          <MapButton
            icon={<Languages size={20} />}
            tooltipText={t('tooltips.selectLanguage')}
            ariaLabel={t('aria.label.selectLanguage')}
          />
        )
      }
      testId={'language-selector-open-button'}
      isMobile={isMobile}
    >
      {languageKeys.map((key) => (
        <button
          key={key}
          onKeyDown={() => handleLanguageSelect(key)}
          onClick={() => handleLanguageSelect(key)}
          className={`w-full cursor-pointer px-2 py-1 text-start text-sm transition hover:bg-gray-200 dark:hover:bg-gray-700 ${
            languageNames[key] === selectedLanguage &&
            'bg-gray-100 font-bold dark:bg-gray-700'
          }`}
        >
          {languageNames[key]}
        </button>
      ))}
    </MapOptionSelector>
  );
}
