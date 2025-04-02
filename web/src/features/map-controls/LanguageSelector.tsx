import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { languageNames } from 'translation/locales';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

type LanguageNamesKey = keyof typeof languageNames;

export function LanguageSelector({
  parentRef,
  onClose,
}: {
  parentRef?: React.RefObject<HTMLElement>;
  onClose?: () => void;
}) {
  const { t, i18n } = useTranslation();
  const languageKeys = Object.keys(languageNames) as Array<LanguageNamesKey>;
  const currentLanguageKey = i18n.language as LanguageNamesKey;
  const [selectedLanguage, setSelectedLanguage] = useState(
    languageNames[currentLanguageKey] ?? 'English'
  );
  const [position, setPosition] = useState({ top: 0, left: 0, width: 0 });
  const dropdownReference = useRef<HTMLDivElement>(null);

  // Calculate position based on parent element
  useEffect(() => {
    if (parentRef?.current) {
      const rect = parentRef.current.getBoundingClientRect();
      setPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
      });
    }
  }, [parentRef]);

  // Handle click outside to close
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownReference.current &&
        !dropdownReference.current.contains(event.target as Node) &&
        parentRef?.current &&
        !parentRef.current.contains(event.target as Node)
      ) {
        onClose?.();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [onClose, parentRef]);

  const handleLanguageSelect = (languageKey: LanguageNamesKey) => {
    i18n.changeLanguage(languageKey);
    setSelectedLanguage(languageNames[languageKey]);
    trackEvent(TrackEvent.LANGUAGE_SELECTED, { language: languageNames[languageKey] });
    onClose?.();
  };

  return (
    <div
      ref={dropdownReference}
      className="fixed z-50 overflow-auto rounded-lg border border-neutral-200 bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-900"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        width: `${position.width}px`,
        maxHeight: '300px',
      }}
    >
      {languageKeys.map((key) => (
        <button
          key={key}
          onKeyDown={(event) => event.key === 'Enter' && handleLanguageSelect(key)}
          onClick={() => handleLanguageSelect(key)}
          className={`w-full cursor-pointer px-2 py-1 text-start text-sm transition hover:bg-neutral-200 dark:hover:bg-neutral-700 ${
            languageNames[key] === selectedLanguage &&
            'bg-neutral-100 font-bold dark:bg-neutral-700'
          }`}
        >
          {languageNames[key]}
        </button>
      ))}
    </div>
  );
}
