import { ReactElement, useState } from 'react';
import { twMerge } from 'tailwind-merge';
import { languageNames } from 'translation/locales';
import { useTranslation } from 'translation/translation';

interface DarkModeSelectorProperties {
  setDarkModeSelectorOpen: (isOpen: boolean) => void;
  className?: string;
}

type LanguageNamesKey = keyof typeof languageNames;

export default function DarkModeSelector({
  setDarkModeSelectorOpen,
  className,
}: DarkModeSelectorProperties): ReactElement {
  const { __, i18n } = useTranslation();
  const darkModeKeys: Array<string> = ['light', 'dark', 'system'];
  const [selectedThemeMode, setSelectedThemeMode] = useState(
    localStorage.getItem('theme') || 'system'
  );

  const handleSetDarkMode = (mode: string) => {
    localStorage.setItem('theme', mode);
    setSelectedThemeMode(mode);
    setDarkModeSelectorOpen(false);
  };
  const darkModeOptions = darkModeKeys.map((option) => {
    return (
      <button
        key={option}
        onKeyDown={() => handleSetDarkMode(option)}
        onClick={() => handleSetDarkMode(option)}
        className={`w-full cursor-pointer px-2 py-1 text-start text-sm ${
          option === selectedThemeMode && 'bg-gray-200   dark:bg-gray-500'
        }`}
      >
        {option}
      </button>
    );
  });
  return (
    <div
      className={twMerge(
        'pointer-events-auto absolute top-[290px] right-10 h-[88px] w-[140px] overflow-auto rounded bg-white py-1 dark:bg-gray-900 dark:[color-scheme:dark]',
        className
      )}
    >
      {darkModeOptions}
    </div>
  );
}
