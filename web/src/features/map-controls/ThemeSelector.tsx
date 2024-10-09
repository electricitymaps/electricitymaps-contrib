import { Button } from 'components/Button';
import { useAtom } from 'jotai';
import { LaptopMinimal, Moon, Palette, Smartphone, Sun } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import trackEvent from 'utils/analytics';
import { ThemeOptions, TrackEvent } from 'utils/constants';
import { themeAtom } from 'utils/state/atoms';

import MapButton from './MapButton';
import MapOptionSelector from './MapOptionSelector';

const ICON_SIZE = 20;

export default function ThemeSelector({ isMobile }: { isMobile?: boolean }) {
  const { t } = useTranslation();
  const [selectedTheme, setSelectedTheme] = useAtom(themeAtom);

  const handleThemeChange = (mode: ThemeOptions) => {
    setSelectedTheme(mode);
    trackEvent(TrackEvent.THEME_SELECTED, { theme: mode });
  };

  const ICONS = {
    light: <Sun size={ICON_SIZE} />,
    dark: <Moon size={ICON_SIZE} />,
    system: isMobile ? (
      <Smartphone size={ICON_SIZE} />
    ) : (
      <LaptopMinimal size={ICON_SIZE} />
    ),
  };

  return (
    <MapOptionSelector
      trigger={
        isMobile ? (
          <Button
            size="lg"
            type="secondary"
            backgroundClasses="w-[330px] h-[45px]"
            icon={<Palette size={ICON_SIZE} />}
          >
            {t('tooltips.changeTheme')}
          </Button>
        ) : (
          <MapButton
            icon={<Palette size={ICON_SIZE} />}
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
