import { Button } from 'components/Button';
import { isInfoModalOpenAtom, isSettingsModalOpenAtom } from 'features/modals/modalAtoms';
import { useAtom, useSetAtom } from 'jotai';
import { useTransition } from 'react';
import { useTranslation } from 'react-i18next';
import { FiWind } from 'react-icons/fi';
import { HiOutlineSun } from 'react-icons/hi';
import { HiCog6Tooth, HiOutlineInformationCircle } from 'react-icons/hi2';
import { MoonLoader } from 'react-spinners';
import trackEvent from 'utils/analytics';
import { ThemeOptions, TimeAverages, ToggleOptions } from 'utils/constants';
import {
  selectedDatetimeIndexAtom,
  solarLayerEnabledAtom,
  solarLayerLoadingAtom,
  themeAtom,
  timeAverageAtom,
  windLayerAtom,
  windLayerLoadingAtom,
} from 'utils/state/atoms';

import ColorblindToggle from './ColorblindToggle';
import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import { LanguageSelector } from './LanguageSelector';
import MapButton from './MapButton';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';
import ThemeSelector from './ThemeSelector';
import ZoomControls from './ZoomControls';

function MobileMapControls() {
  const setIsInfoModalOpen = useSetAtom(isInfoModalOpenAtom);
  const setIsSettingsModalOpen = useSetAtom(isSettingsModalOpenAtom);

  const handleOpenInfoModal = () => setIsInfoModalOpen(true);
  const handleOpenSettingsModal = () => setIsSettingsModalOpen(true);

  return (
    <div className="absolute right-2 top-2 flex space-x-3 pt-[env(safe-area-inset-top)] sm:hidden">
      <Button
        size="lg"
        type="secondary"
        aria-label="open info modal"
        backgroundClasses="bg-white/80 backdrop-blur-sm dark:bg-gray-800/80"
        onClick={handleOpenInfoModal}
        icon={<HiOutlineInformationCircle size={21} />}
      />
      <Button
        size="lg"
        type="secondary"
        aria-label="open settings modal"
        onClick={handleOpenSettingsModal}
        backgroundClasses="bg-white/80 backdrop-blur-sm dark:bg-gray-800/80"
        icon={<HiCog6Tooth size={20} />}
        data-test-id="settings-button-mobile"
      />
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
    enabledAtom: solarLayerEnabledAtom,
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
    />
  );
}

function DesktopMapControls() {
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed =
    selectedDatetime.index === 24 && timeAverage === TimeAverages.HOURLY;

  return (
    <div className="pointer-events-none absolute right-3 top-2 z-30 hidden flex-col items-end md:flex">
      <div className="flex flex-col items-end gap-2">
        <ConsumptionProductionToggle />
        <SpatialAggregatesToggle />
        <ZoomControls />
        <LanguageSelector />
        <ColorblindToggle />
        <ThemeSelector />
        {areWeatherLayersAllowed && (
          <>
            <WeatherButton type="wind" />
            <WeatherButton type="solar" />
          </>
        )}
      </div>
    </div>
  );
}

export default function MapControls() {
  return (
    <>
      <MobileMapControls />
      <DesktopMapControls />
    </>
  );
}
