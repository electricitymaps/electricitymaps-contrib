import { useAtom, useAtomValue } from 'jotai';
import { useTransition } from 'react';
import { useTranslation } from 'react-i18next';
import { FiWind } from 'react-icons/fi';
import { HiOutlineEyeOff, HiOutlineSun } from 'react-icons/hi';
import { MoonLoader } from 'react-spinners';
import trackEvent from 'utils/analytics';
import { ThemeOptions, ToggleOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  isHourlyAtom,
  selectedDatetimeIndexAtom,
  solarLayerAtom,
  solarLayerLoadingAtom,
  themeAtom,
  windLayerAtom,
  windLayerLoadingAtom,
} from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import { LanguageSelector } from './LanguageSelector';
import MapButton from './MapButton';
import MobileButtons from './MobileButtons';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';
import ThemeSelector from './ThemeSelector';

function MobileMapControls() {
  return (
    <div className="absolute right-0 mt-[env(safe-area-inset-top)] p-1 pt-[5px]">
      <MobileButtons />
    </div>
  );
}

export const weatherButtonMap = {
  wind: {
    icon: FiWind,
    iconSize: 18,
    enabledAtom: windLayerAtom,
    loadingAtom: windLayerLoadingAtom,
  },
  solar: {
    icon: HiOutlineSun,
    iconSize: 21,
    enabledAtom: solarLayerAtom,
    loadingAtom: solarLayerLoadingAtom,
  },
};

function WeatherButton({ type }: { type: 'wind' | 'solar' }) {
  const [theme] = useAtom(themeAtom);
  const [, startTransition] = useTransition();
  const { t } = useTranslation();
  const [enabled, setEnabled] = useAtom(weatherButtonMap[type].enabledAtom);
  const [isLoadingLayer, setIsLoadingLayer] = useAtom(weatherButtonMap[type].loadingAtom);
  const isEnabled = enabled === ToggleOptions.ON;
  const Icon = weatherButtonMap[type].icon;
  const tooltipTexts = {
    wind: isEnabled ? t('tooltips.hideWindLayer') : t('tooltips.showWindLayer'),
    solar: isEnabled ? t('tooltips.hideSolarLayer') : t('tooltips.showSolarLayer'),
  };

  const spinnerColor = theme === ThemeOptions.DARK ? 'white' : 'black';
  const weatherId = `${type.charAt(0).toUpperCase() + type.slice(1)}`; // Capitalize first letter

  const onToggle = () => {
    if (isEnabled) {
      trackEvent(`${weatherId} Disabled`);
    } else {
      setIsLoadingLayer(true);
      trackEvent(`${weatherId} Enabled`);
    }

    startTransition(() => {
      setEnabled(isEnabled ? ToggleOptions.OFF : ToggleOptions.ON);
    });
  };

  return (
    <MapButton
      icon={
        isLoadingLayer ? (
          <MoonLoader size={14} color={spinnerColor} />
        ) : (
          <Icon size={weatherButtonMap[type].iconSize} color={isEnabled ? '' : 'gray'} />
        )
      }
      tooltipText={tooltipTexts[type]}
      dataTestId={`${type}-layer-button`}
      className={`${isLoadingLayer ? 'cursor-default' : 'cursor-pointer'}`}
      onClick={isLoadingLayer ? () => {} : onToggle}
      ariaLabel={type == 'wind' ? t('aria.label.windLayer') : t('aria.label.solarLayer')}
      asToggle
    />
  );
}

function DesktopMapControls() {
  const { t } = useTranslation();
  const isHourly = useAtomValue(isHourlyAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed = selectedDatetime.index === 24 && isHourly;

  const handleColorblindModeToggle = () => {
    setIsColorblindModeEnabled(!isColorblindModeEnabled);
    trackEvent('Colorblind Mode Toggled');
  };

  return (
    <div className="pointer-events-none absolute right-3 top-2 z-30 hidden flex-col items-end md:flex">
      <div className="pointer-events-auto mb-16 flex flex-col items-end space-y-2">
        <ConsumptionProductionToggle />
        <SpatialAggregatesToggle />
      </div>
      <div className="mt-5 space-y-2">
        <LanguageSelector />
        <MapButton
          icon={
            <HiOutlineEyeOff
              size={20}
              className={`${isColorblindModeEnabled ? '' : 'opacity-50'}`}
            />
          }
          dataTestId="colorblind-layer-button"
          tooltipText={t('legends.colorblindmode')}
          onClick={handleColorblindModeToggle}
          asToggle
          ariaLabel={t('aria.label.colorBlindMode')}
        />
        {areWeatherLayersAllowed && (
          <>
            <WeatherButton type="wind" />
            <WeatherButton type="solar" />
          </>
        )}
        <ThemeSelector />
      </div>
    </div>
  );
}

export default function MapControls() {
  const isMobile = useIsMobile();
  return isMobile ? <MobileMapControls /> : <DesktopMapControls />;
}
