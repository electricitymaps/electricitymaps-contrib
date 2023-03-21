import { Button } from 'components/Button';
import { isInfoModalOpenAtom, isSettingsModalOpenAtom } from 'features/modals/modalAtoms';
import { useAtom, useSetAtom } from 'jotai';
import { FiWind } from 'react-icons/fi';
import { HiOutlineEyeOff, HiOutlineSun } from 'react-icons/hi';
import { HiCog6Tooth, HiOutlineInformationCircle } from 'react-icons/hi2';
import { MoonLoader } from 'react-spinners';
import { useTranslation } from 'translation/translation';
import trackEvent from 'utils/analytics';
import { TimeAverages, ToggleOptions } from 'utils/constants';
import {
  colorblindModeAtom,
  selectedDatetimeIndexAtom,
  solarLayerEnabledAtom,
  solarLayerLoadingAtom,
  timeAverageAtom,
  windLayerAtom,
  windLayerLoadingAtom,
} from 'utils/state/atoms';
import ConsumptionProductionToggle from './ConsumptionProductionToggle';
import { LanguageSelector } from './LanguageSelector';
import MapButton from './MapButton';
import SpatialAggregatesToggle from './SpatialAggregatesToggle';
import ThemeSelector from './ThemeSelector';

function MobileMapControls() {
  const setIsInfoModalOpen = useSetAtom(isInfoModalOpenAtom);
  const setIsSettingsModalOpen = useSetAtom(isSettingsModalOpenAtom);

  const handleOpenInfoModal = () => setIsInfoModalOpen(true);
  const handleOpenSettingsModal = () => setIsSettingsModalOpen(true);

  return (
    <div className="absolute top-2 right-2 flex space-x-3 pt-[env(safe-area-inset-top)] sm:hidden">
      <Button
        className="m-0 p-3"
        aria-label="open info modal"
        onClick={handleOpenInfoModal}
        icon={<HiOutlineInformationCircle size={21} />}
      />
      <Button
        className="m-0 p-3"
        aria-label="open settings modal"
        onClick={handleOpenSettingsModal}
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
  const { __ } = useTranslation();
  const [enabled, setEnabled] = useAtom(weatherButtonMap[type].enabledAtom);
  const [isLoadingLayer, setIsLoadingLayer] = useAtom(weatherButtonMap[type].loadingAtom);
  const isEnabled = enabled === ToggleOptions.ON;
  const Icon = weatherButtonMap[type].icon;
  const tooltipTexts = {
    wind: isEnabled ? __('tooltips.hideWindLayer') : __('tooltips.showWindLayer'),
    solar: isEnabled ? __('tooltips.hideSolarLayer') : __('tooltips.showSolarLayer'),
  };

  const weatherId = `${type.charAt(0).toUpperCase() + type.slice(1)}`; // Capitalize first letter

  const onToggle = () => {
    if (!isEnabled) {
      setIsLoadingLayer(true);
      trackEvent(`${weatherId} Enabled`);
    } else {
      trackEvent(`${weatherId} Disabled`);
    }

    setEnabled(isEnabled ? ToggleOptions.OFF : ToggleOptions.ON);
  };

  return (
    <MapButton
      icon={
        isLoadingLayer ? (
          <MoonLoader size={14} color="#135836" />
        ) : (
          <Icon size={weatherButtonMap[type].iconSize} color={isEnabled ? '' : 'gray'} />
        )
      }
      tooltipText={tooltipTexts[type]}
      dataTestId={`${type}-layer-button`}
      className={`${isLoadingLayer ? 'cursor-default' : 'cursor-pointer'}`}
      onClick={!isLoadingLayer ? onToggle : () => {}}
      asToggle
    />
  );
}

function DesktopMapControls() {
  const { __ } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [isColorblindModeEnabled, setIsColorblindModeEnabled] =
    useAtom(colorblindModeAtom);

  // We are currently only supporting and fetching weather data for the latest hourly value
  const areWeatherLayersAllowed =
    selectedDatetime.index === 24 && timeAverage === TimeAverages.HOURLY;

  const handleColorblindModeToggle = () => {
    setIsColorblindModeEnabled(!isColorblindModeEnabled);
  };

  return (
    <div className="pointer-events-none absolute right-3 top-3 z-30 hidden flex-col items-end md:flex">
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
          tooltipText={__('legends.colorblindmode')}
          onClick={handleColorblindModeToggle}
          asToggle
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
  return (
    <>
      <MobileMapControls />
      <DesktopMapControls />
    </>
  );
}
