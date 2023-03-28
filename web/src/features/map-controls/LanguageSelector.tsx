import { useState } from 'react';
import { languageNames } from 'translation/locales';
import { useTranslation } from 'translation/translation';
import MapOptionSelector from './MapOptionSelector';
import MapButton from './MapButton';
import { HiLanguage } from 'react-icons/hi2';
import { Button } from 'components/Button';

type LanguageNamesKey = keyof typeof languageNames;

export function LanguageSelector({ isMobile }: { isMobile?: boolean }) {
  const { __, i18n } = useTranslation();
  const languageKeys = Object.keys(languageNames) as Array<LanguageNamesKey>;
  const currentLanguageKey = i18n.language as LanguageNamesKey;
  const [selectedLanguage, setSelectedLanguage] = useState(
    languageNames[currentLanguageKey] ?? 'English'
  );

  const handleLanguageSelect = (languageKey: LanguageNamesKey) => {
    i18n.changeLanguage(languageKey);
    setSelectedLanguage(languageNames[languageKey]);
  };
  return (
    <MapOptionSelector
      trigger={
        isMobile ? (
          <div className="flex w-fit min-w-[232px] items-center justify-center gap-x-2 ">
            <HiLanguage size={21} />
            {__('tooltips.selectLanguage')}
          </div>
        ) : (
          <MapButton
            icon={<HiLanguage size={20} style={{ strokeWidth: '0.5' }} />}
            tooltipText={__('tooltips.selectLanguage')}
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
            'bg-gray-100 font-bold dark:bg-gray-800'
          }`}
        >
          {languageNames[key]}
        </button>
      ))}
    </MapOptionSelector>
  );
}
