import { useFeatureFlag } from 'features/feature-flags/api';
import { useAtom, useAtomValue } from 'jotai';
import { EyeOff, Sun, Wind } from 'lucide-react';
import { useTransition } from 'react';
import { useTranslation } from 'react-i18next';
import { MoonLoader } from 'react-spinners';
import trackEvent from 'utils/analytics';
import { ThemeOptions, ToggleOptions, TrackEvent } from 'utils/constants';
import {
  areWeatherLayersAllowedAtom,
  colorblindModeAtom,
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
import SpatialAggregatesToggle from './SpatialAggregatesToggle';
import ThemeSelector from './ThemeSelector';

function MobileMapControls() {
  return (
    <div className="pointer-events-none absolute right-0 mt-[env(safe-area-inset-top)]"></div>
  );
}

export const weatherButtonMap = {
  wind: {
    icon: Wind,
    iconSize: 20,
    enabledAtom: windLayerAtom,
    loadingAtom: windLayerLoadingAtom,
  },
  solar: {
    icon: Sun,
    iconSize: 20,
    enabledAtom: solarLayerAtom,
    loadingAtom: solarLayerLoadingAtom,
  },
};

function WeatherButton({ type }: { type: 'wind' | 'solar' }) {
  const theme = useAtomValue(themeAtom);
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
      trackEvent(
        weatherId == 'Wind' ? TrackEvent.WIND_DISABLED : TrackEvent.SOLAR_DISABLED
      );
    } else {
      setIsLoadingLayer(true);
      trackEvent(
        weatherId == 'Wind' ? TrackEvent.WIND_ENABLED : TrackEvent.SOLAR_ENABLED
      );
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
          <Icon
            size={weatherButtonMap[type].iconSize}
            className={isEnabled ? '' : 'opacity-50'}
          />
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
  const areWeatherLayersAllowed = useAtomValue(areWeatherLayersAllowedAtom);
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  const handleColorblindModeToggle = () => {
    setIsColorblindModeEnabled(!isColorblindModeEnabled);
    trackEvent(TrackEvent.COLORBLIND_MODE_TOGGLED);
  };

  const isConsumptionOnlyMode = useFeatureFlag('consumption-only');

  return (
    <div className="pointer-events-none absolute right-3 top-2 z-20 mt-[env(safe-area-inset-top)] hidden flex-col items-end md:flex">
      <div className="pointer-events-auto mb-16 flex flex-col items-end space-y-2">
        {!isConsumptionOnlyMode && <ConsumptionProductionToggle />}
        <SpatialAggregatesToggle />
      </div>
      <div className="pointer-events-auto mt-2.5 flex flex-col gap-2 pt-2.5">
        <LanguageSelector />
        <MapButton
          icon={
            <EyeOff
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
