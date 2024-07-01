import { Button } from 'components/Button';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { BsMoonStars } from 'react-icons/bs';
import { HiOutlineComputerDesktop, HiOutlineSun } from 'react-icons/hi2';
import trackEvent from 'utils/analytics';
import { ThemeOptions } from 'utils/constants';
import { themeAtom } from 'utils/state/atoms';

import MapButton from './MapButton';
import MapOptionSelector from './MapOptionSelector';

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
  const { t } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useAtom(themeAtom);

  const handleThemeChange = (mode: ThemeOptions) => {
    setSelectedTheme(mode);
    trackEvent('Theme Selected', { theme: mode });
  };

  return (
    <MapOptionSelector
      trigger={
        isMobile ? (
          <Button
            size="lg"
            type="secondary"
            backgroundClasses="w-[330px] h-[45px]"
            icon={<BsMoonStars size={14} style={{ strokeWidth: '0.2' }} />}
          >
            {t('tooltips.changeTheme')}
          </Button>
        ) : (
          <MapButton
            icon={<BsMoonStars size={14} style={{ strokeWidth: '0.2' }} />}
            tooltipText={t('tooltips.changeTheme')}
            ariaLabel={t('aria.label.changeTheme')}
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
            <span>{t(`themeOptions.${option}`)}</span>
          </div>
        </button>
      ))}
    </MapOptionSelector>
  );
}
