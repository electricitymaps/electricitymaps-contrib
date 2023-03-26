import { useAtom } from 'jotai';
import { BsMoonStars } from 'react-icons/bs';
import { HiOutlineComputerDesktop, HiOutlineSun } from 'react-icons/hi2';
import { useTranslation } from 'translation/translation';
import { ThemeOptions } from 'utils/constants';
import { themeAtom } from 'utils/state/atoms';

import MapButton from './MapButton';
import MapOptionSelector from './MapOptionSelector';
import { Button } from 'components/Button';

const ICONS = {
  light: <HiOutlineSun size={20} />,
  dark: (
    <BsMoonStars
      size={14}
      style={{ strokeWidth: '0.2', marginLeft: 3, marginRight: 2 }}
    />
  ),
  system: <HiOutlineComputerDesktop size={18} />,
};

export default function ThemeSelector({ isMobile }: { isMobile?: boolean }) {
  const { __ } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useAtom(themeAtom);

  const handleThemeChange = (mode: ThemeOptions) => {
    setSelectedTheme(mode);
  };

  return (
    <MapOptionSelector
      trigger={
        isMobile ? (
          <div className="flex w-fit min-w-[232px] items-center justify-center gap-x-2 ">
            <BsMoonStars size={14} style={{ strokeWidth: '0.2' }} />
            {__('tooltips.changeTheme')}
          </div>
        ) : (
          <MapButton
            icon={<BsMoonStars size={14} style={{ strokeWidth: '0.2' }} />}
            tooltipText={__('tooltips.changeTheme')}
          />
        )
      }
      testId="theme-selector-open-button"
      isMobile={isMobile}
    >
      {Object.values(ThemeOptions).map((option) => (
        <button
          key={option}
          onKeyDown={() => handleThemeChange(option)}
          onClick={() => handleThemeChange(option)}
          className={`flex w-full cursor-pointer px-2 py-2 text-start text-sm transition hover:bg-gray-200 dark:hover:bg-gray-700 ${
            option === selectedTheme && 'bg-gray-100 font-bold dark:bg-gray-800'
          }`}
        >
          <div className="flex items-center">
            <div className="mr-2">{ICONS[option]}</div>
            <span>{__(`themeOptions.${option}`)}</span>
          </div>
        </button>
      ))}
    </MapOptionSelector>
  );
}
