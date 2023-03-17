import { useState } from 'react';
import { languageNames } from 'translation/locales';
import { useTranslation } from 'translation/translation';
import MapOptionSelector from './MapOptionSelector';
import MapButton from './MapButton';
import { HiLanguage } from 'react-icons/hi2';

type LanguageNamesKey = keyof typeof languageNames;

export function LanguageSelector() {
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
        <MapButton
          icon={<HiLanguage size={20} style={{ strokeWidth: '0.5' }} />}
          tooltipText={__('tooltips.selectLanguage')}
          dataTestId="language-selector-open-button"
        />
      }
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
