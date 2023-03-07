import { useAtom } from 'jotai';
import { ReactElement } from 'react';
import { BsMoonStars } from 'react-icons/bs';
import { HiOutlineComputerDesktop, HiOutlineSun } from 'react-icons/hi2';
import { twMerge } from 'tailwind-merge';
import { useTranslation } from 'translation/translation';
import { ThemeOptions } from 'utils/constants';
import { themeAtom } from 'utils/state/atoms';

interface DarkModeSelectorProperties {
  setDarkModeSelectorOpen: (isOpen: boolean) => void;
  className?: string;
}

function getIcon(key: string) {
  switch (key) {
    case 'light': {
      return <HiOutlineSun size={20} />;
    }
    case 'dark': {
      return (
        <BsMoonStars
          size={14}
          style={{ strokeWidth: '0.2', marginLeft: 3, marginRight: 2 }}
        />
      );
    }
    case 'system': {
      return <HiOutlineComputerDesktop size={18} />;
    }
    default: {
      return null;
    }
  }
}

export default function DarkModeSelector({
  setDarkModeSelectorOpen,
  className,
}: DarkModeSelectorProperties): ReactElement {
  const { __ } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useAtom(themeAtom);
  const themeOptions = Object.values(ThemeOptions);

  const handleSetDarkMode = (mode: ThemeOptions) => {
    setSelectedTheme(mode);
    setDarkModeSelectorOpen(false);
  };
  const darkModeOptions = darkModeKeys.map((option) => {
    const icon = getIcon(option);
    return (
      <button
        key={option}
        onKeyDown={() => handleSetDarkMode(option)}
        onClick={() => handleSetDarkMode(option)}
        className={`w-full cursor-pointer px-2 py-1 text-start text-sm ${
          option === selectedThemeMode && 'bg-gray-200   dark:bg-gray-500'
        }`}
      >
        <div className="flex">
          <div className="mr-2"> {icon}</div>
          {__(`darkModeButtons.${option}`)}
        </div>
      </button>
    );
  });
  return (
    <div
      className={twMerge(
        'pointer-events-auto absolute top-[290px] right-10 h-[96px] w-[120px] overflow-auto rounded bg-white py-1 dark:bg-gray-900 dark:[color-scheme:dark]',
        className
      )}
    >
      {darkModeOptions}
    </div>
  );
}
